"""TEA test design workflow integration."""

import logging
import re
from pathlib import Path

from .models import TestFramework, TestCase, TestPlan
from .framework_detector import detect_test_framework

logger = logging.getLogger(__name__)


def extract_acceptance_criteria(story_content: str) -> list[dict]:
    """Extract AC from story markdown.

    Args:
        story_content: Story markdown content

    Returns:
        List of AC dicts with id, text, and BDD components
    """
    # Find AC section
    ac_match = re.search(
        r"## Acceptance Criteria\n(.*?)(?=\n## |\Z)",
        story_content,
        re.DOTALL
    )

    if not ac_match:
        return []

    ac_section = ac_match.group(1)
    criteria = []

    # Parse numbered criteria
    for i, match in enumerate(re.finditer(
        r"^\d+\.\s*(.+?)(?=\n\d+\.|\Z)",
        ac_section,
        re.MULTILINE | re.DOTALL
    )):
        ac_text = match.group(1).strip()

        # Extract BDD components
        given = re.search(r"\*\*Given\*\*\s*(.+?)(?=\*\*When\*\*|\Z)", ac_text, re.DOTALL)
        when = re.search(r"\*\*When\*\*\s*(.+?)(?=\*\*Then\*\*|\Z)", ac_text, re.DOTALL)
        then = re.search(r"\*\*Then\*\*\s*(.+?)(?=\*\*And\*\*|\n\n|\Z)", ac_text, re.DOTALL)

        criteria.append({
            "id": f"ac-{i+1}",
            "text": ac_text,
            "given": given.group(1).strip() if given else "",
            "when": when.group(1).strip() if when else "",
            "then": then.group(1).strip() if then else "",
        })

    return criteria


def build_test_design_prompt(
    story_content: str,
    acceptance_criteria: list[dict],
    framework: TestFramework,
) -> str:
    """Build prompt for TEA test-design.

    Args:
        story_content: Full story markdown content
        acceptance_criteria: Extracted acceptance criteria
        framework: Detected test framework

    Returns:
        Formatted prompt for TEA agent
    """
    formatted_criteria = "\n".join([
        f"{i+1}. {ac['text']}"
        for i, ac in enumerate(acceptance_criteria)
    ])

    return f"""
## Test Design Request

### Story Context
{story_content}

### Acceptance Criteria to Cover
{formatted_criteria}

### Target Test Framework
{framework.value}

### Instructions
Generate a comprehensive test plan that:
1. Creates at least one test case per acceptance criterion
2. Uses {framework.value} conventions and patterns
3. Includes setup and teardown instructions
4. Maps each test case to specific acceptance criteria
5. Prioritizes test cases by risk

Output format: Structured test plan with test cases in BDD format.
"""


async def run_tea_agent(prompt: str, agent_path: str) -> str:
    """Run TEA agent with given prompt.

    Args:
        prompt: Formatted prompt for TEA
        agent_path: Path to TEA agent definition

    Returns:
        TEA agent output with test plan in JSON format
    """
    try:
        # Try to use ClaudeSDKClient if available
        from auto_claude.core.client import create_client

        client = create_client()

        # Read agent definition if exists
        agent_def_path = Path(agent_path)
        if agent_def_path.exists():
            agent_context = agent_def_path.read_text()
            full_prompt = f"{agent_context}\n\n{prompt}"
        else:
            logger.warning(f"Agent definition not found at {agent_path}, using prompt only")
            full_prompt = prompt

        # Invoke Claude with TEA context
        response = await client.create_message(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}]
        )

        # Extract text from response
        if hasattr(response, 'content') and response.content:
            return response.content[0].text if isinstance(response.content, list) else str(response.content)

        return str(response)

    except ImportError:
        logger.warning("Claude SDK not available - using structured placeholder")
        # Return a structured placeholder for testing
        return """
{
  "test_cases": [
    {
      "id": "tc-1",
      "name": "Acceptance Criterion 1 Test",
      "description": "Auto-generated test case",
      "acceptance_criteria_id": "ac-1",
      "given": "test precondition",
      "when": "test action",
      "then": "test assertion",
      "priority": "high"
    }
  ],
  "setup_instructions": "Set up test environment",
  "teardown_instructions": "Clean up test data"
}
"""
    except Exception as e:
        logger.error(f"Error invoking TEA agent: {e}")
        raise


def parse_test_plan_output(
    output: str,
    story_id: str,
    framework: TestFramework,
    acceptance_criteria: list[dict],
) -> TestPlan:
    """Parse TEA output into TestPlan.

    Args:
        output: TEA agent output (expected to be JSON)
        story_id: Story identifier
        framework: Test framework
        acceptance_criteria: Original acceptance criteria

    Returns:
        Parsed TestPlan object
    """
    import json

    try:
        # Try to parse as JSON first
        data = json.loads(output)

        # Parse test cases
        test_cases = []
        for tc_data in data.get("test_cases", []):
            test_case = TestCase(
                id=tc_data.get("id", f"tc-{len(test_cases)+1}"),
                name=tc_data.get("name", "Unnamed Test"),
                description=tc_data.get("description", ""),
                acceptance_criteria_id=tc_data.get("acceptance_criteria_id", ""),
                given=tc_data.get("given", ""),
                when=tc_data.get("when", ""),
                then=tc_data.get("then", ""),
                priority=tc_data.get("priority", "medium"),
            )
            test_cases.append(test_case)

        # Build coverage map (AC id -> test case ids)
        coverage_map: dict[str, list[str]] = {}
        for tc in test_cases:
            ac_id = tc.acceptance_criteria_id
            if ac_id:
                if ac_id not in coverage_map:
                    coverage_map[ac_id] = []
                coverage_map[ac_id].append(tc.id)

        test_plan = TestPlan(
            story_id=story_id,
            framework=framework,
            test_cases=test_cases,
            setup_instructions=data.get("setup_instructions", ""),
            teardown_instructions=data.get("teardown_instructions", ""),
            coverage_map=coverage_map,
        )

        logger.info(f"Parsed {len(test_cases)} test cases from TEA output")
        return test_plan

    except json.JSONDecodeError:
        logger.warning("TEA output is not valid JSON, creating minimal test plan")
        # Fallback: Create one test case per AC
        test_cases = []
        coverage_map = {}

        for i, ac in enumerate(acceptance_criteria):
            tc_id = f"tc-{i+1}"
            ac_id = ac["id"]

            test_case = TestCase(
                id=tc_id,
                name=f"Test {ac_id}",
                description=f"Test case for {ac_id}",
                acceptance_criteria_id=ac_id,
                given=ac.get("given", ""),
                when=ac.get("when", ""),
                then=ac.get("then", ""),
                priority="high",
            )
            test_cases.append(test_case)

            if ac_id not in coverage_map:
                coverage_map[ac_id] = []
            coverage_map[ac_id].append(tc_id)

        return TestPlan(
            story_id=story_id,
            framework=framework,
            test_cases=test_cases,
            setup_instructions="Set up test environment",
            teardown_instructions="Clean up test data",
            coverage_map=coverage_map,
        )


async def store_test_plan(test_plan: TestPlan, story_dir: Path) -> None:
    """Store test plan with story artifacts.

    Args:
        test_plan: Generated test plan
        story_dir: Directory containing story file
    """
    import json
    from dataclasses import asdict

    try:
        # Ensure story directory exists
        story_dir.mkdir(parents=True, exist_ok=True)

        # Create test plan filename
        test_plan_file = story_dir / f"{test_plan.story_id}-test-plan.json"

        # Convert TestPlan to dict for JSON serialization
        test_plan_dict = asdict(test_plan)

        # Convert TestFramework enum to string
        test_plan_dict["framework"] = test_plan.framework.value

        # Write to file
        with open(test_plan_file, "w") as f:
            json.dump(test_plan_dict, f, indent=2)

        logger.info(f"Test plan stored at {test_plan_file}")

    except Exception as e:
        logger.error(f"Failed to store test plan: {e}")
        raise


def extract_story_id(story_path: Path) -> str:
    """Extract story ID from story file path.

    Args:
        story_path: Path to story markdown file

    Returns:
        Story identifier (e.g., "5-1-test")
    """
    # Extract from filename: "5-1-tea-test-plan.md" -> "5-1-tea-test-plan"
    return story_path.stem


async def invoke_tea_test_design(
    story_path: Path,
    project_path: Path,
) -> TestPlan:
    """Invoke TEA test-design workflow.

    Args:
        story_path: Path to story markdown file
        project_path: Project root path

    Returns:
        Generated TestPlan

    Raises:
        FileNotFoundError: If story file doesn't exist
        ValueError: If story has no acceptance criteria
    """
    # Validate inputs
    if not story_path.exists():
        raise FileNotFoundError(f"Story file not found: {story_path}")

    if not project_path.exists():
        logger.warning(f"Project path does not exist: {project_path}")

    # Read story content with error handling
    try:
        story_content = story_path.read_text()
    except Exception as e:
        logger.error(f"Failed to read story file {story_path}: {e}")
        raise

    # Detect test framework
    framework = detect_test_framework(project_path)
    logger.info(f"Detected test framework: {framework.value}")

    # Extract acceptance criteria
    acceptance_criteria = extract_acceptance_criteria(story_content)

    # Validate that we have acceptance criteria
    if not acceptance_criteria:
        logger.warning(f"No acceptance criteria found in {story_path}")
        raise ValueError(
            f"Story {story_path.name} has no acceptance criteria. "
            "Cannot generate test plan without acceptance criteria."
        )

    logger.info(f"Extracted {len(acceptance_criteria)} acceptance criteria")

    # Build TEA prompt
    tea_prompt = build_test_design_prompt(
        story_content=story_content,
        acceptance_criteria=acceptance_criteria,
        framework=framework,
    )

    # Invoke Claude with TEA agent context
    try:
        test_plan_output = await run_tea_agent(
            prompt=tea_prompt,
            agent_path="_bmad/bmm/agents/tea.md",
        )
    except Exception as e:
        logger.error(f"TEA agent invocation failed: {e}")
        raise

    # Parse TEA output into TestPlan
    try:
        test_plan = parse_test_plan_output(
            output=test_plan_output,
            story_id=extract_story_id(story_path),
            framework=framework,
            acceptance_criteria=acceptance_criteria,
        )
    except Exception as e:
        logger.error(f"Failed to parse test plan output: {e}")
        raise

    # Store test plan
    try:
        await store_test_plan(test_plan, story_path.parent)
    except Exception as e:
        logger.error(f"Failed to store test plan: {e}")
        # Don't raise - test plan was still generated successfully

    logger.info(
        f"Generated test plan with {len(test_plan.test_cases)} test cases "
        f"covering {len(test_plan.coverage_map)} acceptance criteria"
    )

    return test_plan
