# crew.py

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool  # import CrewAI's BaseTool
from crewai_tools import FileWriterTool  # Import FileWriterTool
from langchain_experimental.utilities import PythonREPL
from pydantic import PrivateAttr
import yaml
import os

# Optionally load environment variables
from dotenv import load_dotenv
load_dotenv()

# ---------------------------
# Custom Tool: Python REPL
# ---------------------------


class PythonREPLCrewTool(BaseTool):
    name: str = "python_repl"
    description: str = (
        "A Python REPL tool. Use this to execute Python code. "
        "Make sure to use print(...) to produce output."
    )

    # declare private attribute to hold the REPL instance
    _repl: PythonREPL = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # bypass Pydantic restriction
        object.__setattr__(self, "_repl", PythonREPL())

    def _run(self, code: str) -> str:
        try:
            result = self._repl.run(code)
            # If nothing printed, result might be None or empty
            if result is None:
                return ""
            return str(result)
        except Exception as e:
            return f"Python REPL error: {e}"

    async def _arun(self, code: str) -> str:
        return self._run(code)


# Instantiate the tools
repl_tool = PythonREPLCrewTool()
file_writer_tool = FileWriterTool(directory="./outputs/reports/")

# ---------------------------
# Crew Definition
# ---------------------------


@CrewBase
class AnalyticsCrew:
    def __init__(self):
        # Load your agent/task configs
        with open("config/agents.yaml", "r") as f:
            self.agents_config = yaml.safe_load(f)
        with open("config/tasks.yaml", "r") as f:
            self.tasks_config = yaml.safe_load(f)

    @agent
    def manager(self) -> Agent:
        return Agent(
            role="Project Manager",
            goal="Efficiently manage the crew and ensure high-quality task completion",
            backstory="You oversee the workflow, delegate tasks, and ensure consistency.",
            allow_delegation=True,
            verbose=True,
            # max_iter=1,
            max_execution_time=300,
        )

    @agent
    def code_executor(self) -> Agent:
        return Agent(
            config=self.agents_config["code_executor"],
            tools=[repl_tool],
            verbose=True,
            # max_retry_limit=1,
            # max_iter=1,
        )

    @agent
    def report_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["report_writer"],
            tools=[file_writer_tool, repl_tool],
            verbose=True,
            # max_retry_limit=1,
            max_iter=1
        )

    @task
    def code_executorTask(self) -> Task:
        return Task(
            config=self.tasks_config["code_execution_task"],
            agent=self.code_executor()
        )

    @task
    def report_writingTask(self) -> Task:
        return Task(
            config=self.tasks_config["report_writing_task"],
            agent=self.report_writer(),
            context=[
                self.code_executorTask()
            ],
        )

    @crew
    def crew(self) -> Crew:
        # exclude manager from the agents list if you also specify manager_agent
        agent_list = [
            # self.data_profiler(),
            self.code_executor(),
            self.report_writer()]
        return Crew(
            agents=agent_list,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager(),
            verbose=True,
            memory=False,  # Disable memory to ensure single execution
            max_iter=1,    # Ensure tasks run only once
        )
