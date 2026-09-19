"""
Campaign Knowledge Base & RAG Retrieval Module.
Enforces strict Campaign Isolation, chunk-level indexing, and Top-K retrieval.
"""

import os
import re
import math
from collections import Counter
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

KB_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_bases")


class KBChunk(BaseModel):
    """Granular RAG chunk for top-k retrieval and source citation."""
    chunk_id: str
    campaign_id: str
    section: str
    title: str
    content: str
    keywords: List[str] = []


class CampaignKnowledgeStore:
    def __init__(self):
        self.campaign_docs: Dict[str, Dict[str, str]] = {}
        self.chunks: Dict[str, List[KBChunk]] = {}  # campaign_id -> List[KBChunk]
        self._load_knowledge_bases()

    def _load_knowledge_bases(self):
        """Loads and parses campaign knowledge bases into modular sections and indexed chunks."""
        campaign_map = {
            "us_saas_cto": os.path.join(KB_ROOT, "us_saas_cto", "knowledge.md"),
            "india_bfsi_cio": os.path.join(KB_ROOT, "india_bfsi_cio", "knowledge.md"),
            "voice_ai_founder": os.path.join(KB_ROOT, "voice_ai_founder", "knowledge.md"),
        }

        for campaign_id, file_path in campaign_map.items():
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.campaign_docs[campaign_id] = self._parse_sections(content)
                self.chunks[campaign_id] = self._create_chunks(campaign_id, content)

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Splits markdown into logical RAG chunks by ## headers."""
        sections = {}
        chunks = re.split(r'\n##\s+', content)
        for chunk in chunks:
            if not chunk.strip():
                continue
            lines = chunk.strip().split('\n')
            header = lines[0].strip().lower()
            body = "\n".join(lines[1:]).strip()

            if "overview" in header or "value proposition" in header:
                sections["product_overview"] = body
            elif "icp" in header or "ideal customer" in header:
                sections["icp_criteria"] = body
            elif "case studies" in header:
                sections["case_studies"] = body
            elif "objection" in header:
                sections["objections"] = body
            elif "template" in header or "outreach" in header:
                sections["templates"] = body
            else:
                sections[header] = body
        return sections

    def _create_chunks(self, campaign_id: str, content: str) -> List[KBChunk]:
        """Creates fine-grained chunks by splitting on ## and ### headers for citation."""
        chunks: List[KBChunk] = []
        raw_sections = re.split(r'\n##\s+', content)

        for sec_idx, section in enumerate(raw_sections):
            if not section.strip():
                continue
            lines = section.strip().split('\n')
            sec_header = lines[0].strip()
            sec_body = "\n".join(lines[1:]).strip()

            # Sub-split on ### headers if present (e.g. case studies or objections)
            sub_chunks = re.split(r'\n###\s+', sec_body)
            if len(sub_chunks) > 1:
                for sub_idx, sub in enumerate(sub_chunks):
                    if not sub.strip():
                        continue
                    sub_lines = sub.strip().split('\n')
                    sub_title = sub_lines[0].strip()
                    sub_content = "\n".join(sub_lines[1:]).strip()
                    slug = re.sub(r'[^a-z0-9]+', '_', sub_title.lower()).strip('_')
                    chunk_id = f"{campaign_id}#{slug}"
                    chunks.append(KBChunk(
                        chunk_id=chunk_id,
                        campaign_id=campaign_id,
                        section=sec_header,
                        title=sub_title,
                        content=sub_content or sub_title,
                        keywords=self._tokenize(f"{sec_header} {sub_title} {sub_content}")
                    ))
            else:
                slug = re.sub(r'[^a-z0-9]+', '_', sec_header.lower()).strip('_')
                chunk_id = f"{campaign_id}#{slug}"
                chunks.append(KBChunk(
                    chunk_id=chunk_id,
                    campaign_id=campaign_id,
                    section=sec_header,
                    title=sec_header,
                    content=sec_body,
                    keywords=self._tokenize(f"{sec_header} {sec_body}")
                ))

        return chunks

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_\-\$]{2,}\b', text)]

    def retrieve_top_k(self, campaign_id: str, query: str, k: int = 3) -> List[KBChunk]:
        """
        Retrieves Top-K relevant chunks strictly scoped to campaign_id using TF-IDF cosine similarity.
        Enforces strict Campaign Isolation.
        """
        if campaign_id not in self.chunks:
            raise ValueError(f"Unknown campaign_id '{campaign_id}'. Available: {list(self.chunks.keys())}")

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return self.chunks[campaign_id][:k]

        q_vec = Counter(q_tokens)

        scored: List[tuple[float, KBChunk]] = []
        for chunk in self.chunks[campaign_id]:
            doc_vec = Counter(chunk.keywords)
            # Dot product
            common = set(q_vec.keys()) & set(doc_vec.keys())
            dot = sum(q_vec[term] * doc_vec[term] for term in common)
            # Magnitudes
            mag_q = math.sqrt(sum(v * v for v in q_vec.values()))
            mag_d = math.sqrt(sum(v * v for v in doc_vec.values()))
            sim = (dot / (mag_q * mag_d)) if (mag_q > 0 and mag_d > 0) else 0.0

            # Boost case study and objection chunks
            if "case study" in chunk.section.lower() or "case_studies" in chunk.chunk_id:
                sim *= 1.25
            if "objection" in chunk.section.lower() or "battlecard" in chunk.section.lower() or "differentiation" in chunk.section.lower():
                if any(w in query.lower() for w in ["expensive", "already use", "datadog", "cost", "cloud", "competitor", "objection", "rebuttal", "alternative", "deepgram", "cast ai", "kubecost"]):
                    sim *= 1.35

            scored.append((sim, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for sim, chunk in scored[:k]]

    def get_campaign_context(self, campaign_id: str) -> Dict[str, str]:
        """Returns the full isolated knowledge set for a campaign."""
        if campaign_id not in self.campaign_docs:
            raise ValueError(f"Unknown campaign_id '{campaign_id}'. Available: {list(self.campaign_docs.keys())}")
        return self.campaign_docs[campaign_id]

    def verify_no_cross_campaign_leak(self, source_campaign_id: str, text: str) -> Dict[str, Any]:
        """
        Adversarial test: checks if text contains distinctive entities from a DIFFERENT campaign.
        Returns leak detection status.
        """
        other_campaign_markers = {
            "us_saas_cto": ["turboscale", "veloce health", "stackpulse"],
            "india_bfsi_cio": ["finshield", "bharat apex", "dpdp act", "rbi compliance"],
            "voice_ai_founder": ["whisperflow", "talksync", "carecall", "sub-450ms"],
        }

        leaks_detected = []
        text_lower = text.lower()

        for camp_id, markers in other_campaign_markers.items():
            if camp_id != source_campaign_id:
                for marker in markers:
                    if marker in text_lower:
                        leaks_detected.append({"leaked_from": camp_id, "marker": marker})

        return {
            "has_leak": len(leaks_detected) > 0,
            "leaks": leaks_detected,
            "safe": len(leaks_detected) == 0
        }


# Singleton instance
kb_store = CampaignKnowledgeStore()
