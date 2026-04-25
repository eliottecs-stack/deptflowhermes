from __future__ import annotations

from deptflow_sdr.domain.models import Lead, LeadScore, PreparedMessage
from deptflow_sdr.agents.qa import QAAgent


def _first_name(lead: Lead) -> str:
    if lead.first_name:
        return lead.first_name
    if lead.full_name:
        return lead.full_name.split()[0]
    return "Bonjour"


class MessageWriter:
    def __init__(self, offer_description: str, call_to_action: str):
        self.offer_description = offer_description.strip()
        self.call_to_action = call_to_action.strip() or "Est-ce un sujet que vous regardez en ce moment ?"
        self.qa = QAAgent()

    def first_message(self, lead: Lead, score: LeadScore) -> PreparedMessage:
        first_name = _first_name(lead)
        context = ""
        if lead.company_name:
            context = f"J'ai vu votre rôle chez {lead.company_name}. "
        elif lead.headline:
            context = "Votre profil m'a semblé pertinent. "

        value = self.offer_description or "J'aide des équipes B2B à structurer une prospection plus fiable"
        body = f"Bonjour {first_name}, {context}{value}. {self.call_to_action}"
        body = " ".join(body.split())

        ok, notes = self.qa.review_message(lead, body)
        return PreparedMessage(
            lead_key=lead.key(),
            message_type="first_message",
            body=body,
            approved_by_qa=ok,
            qa_notes=notes,
        )

    def follow_up(self, lead: Lead) -> PreparedMessage:
        first_name = _first_name(lead)
        body = f"Bonjour {first_name}, je me permets une courte relance. Est-ce pertinent d'en discuter ou mieux vaut que je clôture le sujet ?"
        ok, notes = self.qa.review_message(lead, body)
        return PreparedMessage(
            lead_key=lead.key(),
            message_type="follow_up",
            body=body,
            approved_by_qa=ok,
            qa_notes=notes,
        )
