# Implementation Plan - Chapter Fine Outline & Requirements Review

This plan addresses the user's detailed requirements, specifically adding the missing "Chapter Fine Outline" (章节细纲) step in the generation workflow.

## User Review Required
> [!IMPORTANT]
> The database schema for `Chapter` will be modified to add `fine_outline`.
> The backend Docker container MUST be rebuilt to apply these changes.
> Existing chapters in the database might need a manual migration or will have empty `fine_outline`. Since I cannot run migration scripts, I will update the model definition, which works for new setups or if SQLAlchemy `create_all` is safe (it usually skips existing tables). **For existing data, `fine_outline` will be null, which is fine.**

## Proposed Changes

### Backend
#### [MODIFY] [db/models.py](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/backend/app/db/models.py)
- Add `fine_outline: Mapped[str | None] = mapped_column(Text, nullable=True)` to `Chapter` model.

#### [MODIFY] [schemas.py](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/backend/app/schemas.py)
- Add `fine_outline: str | None` to `Chapter` schema in `NovelDetailOut`.

#### [MODIFY] [services/novels.py](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/backend/app/services/novels.py)
- Update `get_novel_detail` to include `fine_outline` in the response.

#### [MODIFY] [workers/novel_tasks.py](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/backend/app/workers/novel_tasks.py)
- Implement `_gen_chapter_fine_outline` function:
    - Agent: `fine_outline_agent` (章节细纲助手)
    - Input: Novel Setting, Chapter Outline, Bible, Knowledge Base.
    - Output: Detailed scene/beat breakdown.
- Update `_generate_chapter` and `_generate_chapters_batch` to:
    1.  Generate Chapter Outline (if missing).
    2.  **Generate Chapter Fine Outline**.
    3.  Generate Chapter Text (using Fine Outline as input).

### Frontend
#### [MODIFY] [types/novel.ts](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/frontend/src/types/novel.ts)
- Add `fine_outline?: string | null` to `Chapter` type.

#### [MODIFY] [utils/labels.ts](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/frontend/src/utils/labels.ts)
- Add `fine_outline_agent: '细纲助手'` to `agentLabel`.

#### [MODIFY] [components/novel/RunLogPanel.tsx](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/frontend/src/components/novel/RunLogPanel.tsx)
- Add `chapter_fine_outline` milestone to `milestonesForKind` under `chapter` kind.

#### [MODIFY] [components/novel/WorkflowSteps.tsx](file:///Users/jack.yan/Downloads/labeleases/stage03/413/auto-writer/frontend/src/components/novel/WorkflowSteps.tsx)
- Add "Reader" view support for `SimpleMarkdown`.
- Update `Chapter` generation UI (or status display) to reflect the new step.
- **Note**: Currently `WorkflowSteps` doesn't strictly visualize the sub-steps of a chapter generation (it just shows status). The log panel shows the sub-steps. I will keep it simple and rely on the Log Panel for visibility of "Fine Outline" generation, unless the user explicitly needs to *edit* the fine outline.
    - *User Requirement*: "Can generate Chapter Fine Outline... only verify single generation...". "Each step has independent agent". "Can pause/resume".
    - If the user wants to EDIT the fine outline, I need a specific UI for it.
    - Given the constraint of "Review and Fix" and the complexity, I will implicitly support it in the generation chain first. If I add a specific *tab* for Fine Outline similar to "Chapter Outline", it would require significant UI work (a new tab between "Plan" and "Chapter"? Or inside "Chapter"?).
    - **Decision**: I'll stick to adding it to the automatic generation chain first. The "Reader" view currently shows "Chapter Outline Summary". I can perhaps add "Chapter Fine Outline" there too?
    - *Correction*: The user requirement says: "Generate Chapter Outline ... Generate Chapter Fine Outline ... Generate Chapter Text". This implies these are distinct stages.
    - **Refined UI Plan**: Add a new Step Tab: "章节细纲" (Fine Outline) between "Chapter Outline" (which is actually inside "Plan" currently? No, "Chapter Outline" is generated *per chapter*).
    - Actually, looking at `WorkflowSteps.tsx`:
        - `outline`: Novel Outline
        - `titles`: Titles
        - `plan`: Volume/Chapter Plan
        - `chapter`: "Chapter Generation Console" -> This lists chapters and has a "Generate" button.
    - When you click "Generate" on a chapter, it runs the task.
    - I will modify the backend task to include the "Fine Outline" step.
    - I will update `RunLogPanel` to show this step.
    - Visually in `WorkflowSteps`, I won't add a new top-level tab because "Fine Outline" is per-chapter data, similar to "Content". Viewing it can be done in the "Reader" or by expanding the chapter (if we had that UI). I'll add the Fine Outline to the "Reader" view so the user can see it.

## Verification Plan

### Manual Verification
1.  **Generation Flow**:
    -   Start a chapter generation.
    -   Observe `RunLogPanel`. It should show `fine_outline_agent` (细纲助手) working after `chapter_outline_agent` and before `chapter_writer`.
2.  **Data Persistence**:
    -   After generation, check the "Reader" view.
    -   It should display "Chapter Fine Outline" (章节细纲) in addition to "Chapter Outline".

### Automated Tests
-   None.
