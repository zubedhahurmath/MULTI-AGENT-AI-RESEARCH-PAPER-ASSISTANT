import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("pdf_extractor")

try:
    import pymupdf as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False


class PDFExtractorService:
    """Service to parse, validate, and extract structured text & metadata from PDF research papers."""

    # Common academic paper section heading patterns
    SECTION_PATTERNS = {
        "abstract": re.compile(r"^\s*(?:abstract|summary)\b", re.IGNORECASE),
        "introduction": re.compile(r"^\s*(?:(?:\d+|[I|V|X]+)\.?\s*)?(?:introduction|background)\b", re.IGNORECASE),
        "related_work": re.compile(r"^\s*(?:(?:\d+|[I|V|X]+)\.?\s*)?(?:related\s+work|literature\s+review)\b", re.IGNORECASE),
        "methodology": re.compile(r"^\s*(?:(?:\d+|[I|V|X]+)\.?\s*)?(?:methodology|method|proposed\s+(?:method|approach|system|architecture)|materials\s+and\s+methods)\b", re.IGNORECASE),
        "experiments": re.compile(r"^\s*(?:(?:\d+|[I|V|X]+)\.?\s*)?(?:experiments|experimental\s+setup|evaluation|results\s+and\s+discussion|results)\b", re.IGNORECASE),
        "discussion": re.compile(r"^\s*(?:(?:\d+|[I|V|X]+)\.?\s*)?(?:discussion|limitations)\b", re.IGNORECASE),
        "conclusion": re.compile(r"^\s*(?:(?:\d+|[I|V|X]+)\.?\s*)?(?:conclusion|conclusions|concluding\s+remarks)\b", re.IGNORECASE),
        "references": re.compile(r"^\s*(?:(?:\d+|[I|V|X]+)\.?\s*)?(?:references|bibliography)\b", re.IGNORECASE),
    }

    @staticmethod
    def is_valid_pdf_file(file_path: str) -> bool:
        """Validate if file exists and starts with standard PDF header bytes."""
        if not os.path.exists(file_path):
            return False
        try:
            with open(file_path, "rb") as f:
                header = f.read(5)
                return header.startswith(b"%PDF-")
        except Exception:
            return False

    def extract_paper(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text, sections, and metadata from a research paper PDF.
        Handles encrypted, corrupted, and scanned documents gracefully.
        """
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not installed in the environment.")

        if not self.is_valid_pdf_file(file_path):
            return {
                "success": False,
                "error": "The uploaded file is not a valid or readable PDF document.",
                "is_scanned": False,
                "requires_ocr": False,
                "metadata": {},
                "raw_text": "",
                "sections": {},
            }

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            return {
                "success": False,
                "error": f"Corrupted or invalid PDF file: {str(e)}",
                "is_scanned": False,
                "requires_ocr": False,
                "metadata": {},
                "raw_text": "",
                "sections": {},
            }

        try:
            # Check for password encryption
            if doc.is_encrypted:
                return {
                    "success": False,
                    "error": "The PDF is password protected. Please upload an unprotected research paper.",
                    "is_scanned": False,
                    "requires_ocr": False,
                    "metadata": {},
                    "raw_text": "",
                    "sections": {},
                }

            total_pages = len(doc)
            if total_pages == 0:
                return {
                    "success": False,
                    "error": "The PDF contains no pages.",
                    "is_scanned": False,
                    "requires_ocr": False,
                    "metadata": {},
                    "raw_text": "",
                    "sections": {},
                }

            # Extract basic PDF metadata
            doc_meta = doc.metadata or {}
            metadata = {
                "title": doc_meta.get("title", "").strip() or None,
                "authors": doc_meta.get("author", "").strip() or None,
                "subject": doc_meta.get("subject", "").strip() or None,
                "keywords": doc_meta.get("keywords", "").strip() or None,
                "total_pages": total_pages,
            }

            # Collect raw page texts
            page_texts = []
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                page_texts.append(page.get_text("text"))

            combined_raw_text = "\n\n".join(page_texts).strip()

            # Clean common artifacts (de-hyphenate words broken by line endings)
            cleaned_text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", combined_raw_text)

            # Heuristic check: is this a scanned PDF (image only without embedded text)?
            total_chars = len(cleaned_text.replace(" ", "").replace("\n", ""))
            if total_chars < 150:
                return {
                    "success": True,
                    "is_scanned": True,
                    "requires_ocr": True,
                    "error": "Document contains minimal extractable text. It appears to be a scanned image-based PDF requiring OCR.",
                    "metadata": metadata,
                    "raw_text": cleaned_text,
                    "sections": {},
                }

            # Heuristic title fallback: if metadata title is empty, look at first few lines of page 1
            if not metadata["title"] and page_texts:
                first_lines = [line.strip() for line in page_texts[0].split("\n") if len(line.strip()) > 5]
                if first_lines:
                    metadata["title"] = first_lines[0][:200]

            # Segment text into identifiable academic sections
            sections = self._organize_sections(cleaned_text)

            return {
                "success": True,
                "is_scanned": False,
                "requires_ocr": False,
                "error": None,
                "metadata": metadata,
                "raw_text": cleaned_text,
                "sections": sections,
            }

        except Exception as e:
            logger.error(f"Unexpected error extracting PDF: {e}")
            return {
                "success": False,
                "error": f"Failed to extract PDF content: {str(e)}",
                "is_scanned": False,
                "requires_ocr": False,
                "metadata": {},
                "raw_text": "",
                "sections": {},
            }
        finally:
            doc.close()

    def _organize_sections(self, text: str) -> Dict[str, str]:
        """Organize flat text into semantic academic sections using regex heading matching."""
        lines = text.split("\n")
        sections: Dict[str, list[str]] = {
            "abstract": [],
            "introduction": [],
            "related_work": [],
            "methodology": [],
            "experiments": [],
            "discussion": [],
            "conclusion": [],
            "references": [],
            "other": []
        }

        current_section = "other"

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            matched_section = None
            # Only test headings if line is reasonably short (headings rarely exceed 80 chars)
            if len(trimmed) < 80:
                for sec_key, pattern in self.SECTION_PATTERNS.items():
                    if pattern.search(trimmed):
                        matched_section = sec_key
                        break

            if matched_section:
                current_section = matched_section
            else:
                sections[current_section].append(trimmed)

        # Join lines for each section
        result: Dict[str, str] = {}
        for sec_name, sec_lines in sections.items():
            content = " ".join(sec_lines).strip()
            if content:
                result[sec_name] = content

        return result


# Singleton instance
pdf_extractor_service = PDFExtractorService()
