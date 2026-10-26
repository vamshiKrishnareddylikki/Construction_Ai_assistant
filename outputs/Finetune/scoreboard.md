# Scoreboard: Base vs. Fine-tuned vs. RAG

Graded on 15 test questions the fine-tuned model never saw during training.

| System | Score | Correct | Partial | Incorrect | Hallucinations |
|---|---|---|---|---|---|
| Base model (Qwen3-0.6B) | **50.0%** | 6 | 3 | 6 | 8 |
| Fine-tuned (Qwen3-0.6B + LoRA) | **26.7%** | 3 | 2 | 10 | 12 |
| RAG bot (document lookup + LLM) V| **96.7%** | 14 | 1 | 0 | 0 |

## Every question

**Q:** Will the Subcontractor be paid for work done without a signed Change Order?  
**Reference:** No, work performed without a signed Change Order will not be paid.  
- *base* (correct): No, the Subcontractor will not be paid for work done without a signed Change Order. A signed Change Order is required to ensure proper documentation and accountability for any work performed.
- *finetuned* (correct): No, the Owner is responsible for all payments, but a signed Change Order is required to receive payment for the submittal.
- *rag* (correct): No. Work performed without a signed Change Order will not be paid. [Source 1]

**Q:** When is fall protection required on a job site?  
**Reference:** Fall protection is required for any work 6 feet or more above a lower level.  
- *base* (partial): Fall protection is required on all jobs that involve working at heights, including scaffolding, ladders, or any structure that poses a risk of falling.
- *finetuned* (incorrect ⚠️ hallucination): Fall protection is required at all times near a high-risk job site.
- *rag* (correct): Fall protection is required for any work that is **6 feet or more above a lower level**【Source 1】.

**Q:** Do we need a personal fall arrest system for work at 5 feet?  
**Reference:** No, fall protection is only required for work 6 feet or more above a lower level.  
- *base* (correct ⚠️ hallucination): No, there is no requirement for a personal fall arrest system (PFAS) at 5 feet for work in South Florida. The safety requirements for fall arrest systems depend on the height and the specific work environment. For heights above 10 feet, a PFAS is typically required.
- *finetuned* (incorrect ⚠️ hallucination): Yes, fall arrest systems are required at heights of 5 feet or more.
- *rag* (correct): No. Fall protection (including a personal fall arrest system) is only required for work **6 feet or more** above a lower level【Source 1】.

**Q:** Do we need to provide daily updates on punch‑list items?  
**Reference:** No, updates are tracked weekly by the project manager, not daily.  
- *base* (incorrect ⚠️ hallucination): Yes, we typically provide daily updates on punch list items to ensure transparency and compliance with project requirements.
- *finetuned* (incorrect ⚠️ hallucination): Yes, daily updates are required for all punch‑list items.
- *rag* (correct): No. The project manager is required to track punch‑list status **weekly**, not daily, until all items are closed. 【Source 1】

**Q:** Is there a deadline for submitting impact‑rated windows on a Florida job?  
**Reference:** Yes, they must be included in the submittal within the first 30 days and carry a valid Florida Product Approval or Miami‑Dade NOA.  
- *base* (incorrect ⚠️ hallucination): There is no specific deadline for submitting impact-rated windows on a Florida job. The submission process typically depends on the company's internal policies and the specific requirements of the project. If you need assistance with submitting, please contact the relevant department or provide more
- *finetuned* (incorrect ⚠️ hallucination): Submit within 10‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑
- *rag* (partial): Yes. Impact‑rated windows (a long‑lead item) must be included in the submittal package and submitted within the first **30 days** of the subcontract. [Source 1]

**Q:** How much retainage will be held on a payment when the project is at 60% completion?  
**Reference:** Since the project is past 50% completion, retainage is reduced to 5% on each payment.  
- *base* (incorrect ⚠️ hallucination): At 60% completion, the retainage is typically **10%** of the total contract value.
- *finetuned* (incorrect ⚠️ hallucination): Retainage of 3% is held on each payment when the project is at 60% completion.
- *rag* (correct): The retainage is reduced to **5%** once the project passes the 50% completion threshold, so at 60% completion a payment will have a 5% retainage held. [Source 1]

**Q:** Who issues the Certificate of Substantial Completion?  
**Reference:** The architect issues the Certificate of Substantial Completion, and it includes an attached punch list of remaining items.  
- *base* (incorrect ⚠️ hallucination): The Certificate of Substantial Completion is issued by the owner of the project.
- *finetuned* (partial ⚠️ hallucination): The certificate is issued by the architect or the superintendent of the subgrade.
- *rag* (correct): The architect issues the Certificate of Substantial Completion【Source 1】.

**Q:** Do we need to wear hard hats on the site at all times?  
**Reference:** Yes, hard hats are required at all times on site.  
- *base* (correct): At all times, hard hats are required for safety on-site.
- *finetuned* (correct): Yes, all work sites must wear safety goggles, a hard hat, and a face mask.
- *rag* (correct): Yes. Hard hats are required at all times while on the site [Source 1].

**Q:** Which lien documents are needed from us and our suppliers?  
**Reference:** Final lien waivers from the subcontractor and all suppliers must be provided (item 4).  
- *base* (partial): We require lien documents from both you and your suppliers to ensure proper documentation and compliance with legal requirements. Please provide the necessary documents so we can assist you effectively.
- *finetuned* (incorrect ⚠️ hallucination): The Owner’s lien certificate and the Subsidiary lien certificate are required.
- *rag* (correct): The required lien documents are the **final lien waivers** from both the subcontractor (your company) and all of the suppliers. [Source 1]

**Q:** How far must a ladder extend above the landing surface?  
**Reference:** Ladders must extend at least 3 feet above the landing surface.  
- *base* (correct): A ladder must extend at least 3 feet (90 cm) above the landing surface to ensure safety and prevent tripping hazards.
- *finetuned* (incorrect ⚠️ hallucination): A ladder must extend at least 10 feet above the landing surface.
- *rag* (correct): Ladders must extend at least **3 feet** above the landing surface【Source 1】.

**Q:** Does an RFI response automatically approve extra cost?  
**Reference:** No; an RFI response does not authorize extra cost—any cost change requires a Change Order request.  
- *base* (correct): No, an RFI response does **not** automatically approve extra costs. Builders typically need to review and approve any additional costs separately, depending on the specific terms of the RFI and the company's internal approval process.
- *finetuned* (incorrect ⚠️ hallucination): No, an RFI response only approves extra cost if the response states the cost is reasonable and approved.
- *rag* (correct): No. An RFI response does **not** authorize any extra cost; if the answer impacts cost or schedule, a separate Change Order request is required【Source 1】.

**Q:** If a subcontractor misses the 30‑day deadline, is that allowed?  
**Reference:** The procedure requires completion within 30 days, so missing that deadline would be non‑compliant with the closeout requirements.  
- *base* (correct): No, a subcontractor is not allowed to miss the 30-day deadline. The company policy explicitly states that all subcontractors must adhere to the 30-day deadline. If a subcontractor fails to meet this requirement, they may be subject to penalties or termination.
- *finetuned* (correct): No; missing the 30‑day deadline results in a penalty of $1,000 per missing day.
- *rag* (correct): No. Long‑lead items must be submitted within the first 30 days of the subcontract; missing that deadline would be a breach of the requirement. [Source 3]

**Q:** When is the final retainage released?  
**Reference:** Final retainage is released after closeout documents are received and approved.  
- *base* (partial ⚠️ hallucination): The final retainage is typically released **after the project is completed** and all work is inspected and approved. This is usually around **10 to 14 days after the project is delivered**. If you have a specific timeline in mind, please provide more details so I can assist you better.
- *finetuned* (partial ⚠️ hallucination): Final retainage is released 10 days after the Closeout.
- *rag* (correct): The final retainage is released **after all closeout documents have been received and approved**【Source 1】. This is confirmed in the payment conditions, which state that the final retainage is released once the closeout documents are approved【Source 2】.

**Q:** How is the length of a weather‑delay extension calculated?  
**Reference:** The extension equals the number of working days lost due to the excusable weather event.  
- *base* (incorrect ⚠️ hallucination): The length of a weather-delay extension is typically calculated based on the distance between the original construction site and the location where the delay is expected to occur. This distance is often determined by the distance between the original construction site and the location where the dela
- *finetuned* (incorrect ⚠️ hallucination): The length is calculated as the difference between the original project start date and the extension end date, with the result being a positive or negative number.
- *rag* (correct): The extension equals the number of **working days lost** due to the weather event — the Subcontractor receives a time extension matching those lost days【Source 1】.

**Q:** How long does the architect have to answer a standard RFI?  
**Reference:** The architect’s standard response time is 5 business days.  
- *base* (incorrect ⚠️ hallucination): The architect has 10 business days to respond to a standard RFI.
- *finetuned* (incorrect ⚠️ hallucination): The architect has 48 hours to respond.
- *rag* (correct): The architect must respond to a standard RFI within **5 business days**【Source 1】.
