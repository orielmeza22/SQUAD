"""Quality Assurance Agent for SQUAD."""

from typing import Dict, Any

from .base import BaseAgent
from .prompts import code_review_prompt, fix_prompt, qa_devops_prompt
from ..tools.sys_tools import SysTools


class QAAgent(BaseAgent):
    """Agent responsible for code quality validation, review and testing.

    Phase 2: reviews generated files for critical issues; if flagged, triggers
    a fix pass.  Then generates test scripts and CI/CD pipelines.
    """

    def __init__(self):
        super().__init__(
            name="QA",
            description="Validates code quality, runs code review and generates tests"
        )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review code, fix critical issues and generate tests.

        Args:
            context: Must contain ``plan`` and ``created_files``; should
                contain ``target_model``.

        Returns:
            Dictionary with ``status``, whether critical issues were found,
            and the list of written test/CI files.
        """
        plan = context.get("plan", "")
        created_files = context.get("created_files", [])
        model = self._resolve_model(context)

        # --- Code Review ---
        review_prompt = code_review_prompt(plan, created_files)
        code_review = self.generate(model=model, prompt=review_prompt)

        critical = "SÍ_CRITICO" in code_review.upper()

        if critical:
            fix_prompt_text = fix_prompt(code_review)
            fix_out = self.generate(model=model, prompt=fix_prompt_text)
            SysTools.extract_and_write_multifile(fix_out)

        # --- Syntax Linter pass ---
        syntax_errors: list = []
        for cf in created_files:
            full_path = SysTools.WORKSPACE and cf and (SysTools.WORKSPACE + "/" + cf)
            if full_path:
                import os as _os
                if _os.path.exists(full_path):
                    ok, msg = SysTools.run_linter(full_path)
                    if not ok:
                        syntax_errors.append(f"Archivo: {cf}\nError: {msg}")

        # --- QA & DevOps test/CI generation ---
        qa_prompt = qa_devops_prompt()
        test_out = self.generate(model=model, prompt=qa_prompt)
        qa_files: list = []
        if test_out:
            qa_files = SysTools.extract_and_write_multifile(test_out)

        return {
            "status": "success",
            "critical_found": critical,
            "code_review": code_review,
            "syntax_errors": syntax_errors,
            "files": qa_files,
        }
