"""
Defines the base Agent class used by all agents in the project.

The base class provides shared functionality for initializing agents and logging their activities.
Specialized agents, such as OpportunityExtractionAgent and OpportunityAssistantAgent, inherit from
this class and implement their own responsibilities.
"""


import logging


class Agent:
    """
    Base class for all the agents.

    Attributes:
        name: Human-readable name of the agent.
        logger: Logger instance used to record agent activities.
    """

    name = 'Base Agent'


    def __init__(self) -> None:
        """
        Initializes the agent and configures its logger

        Creates a logger associated with the agent's class and records an initialization message.
        """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.log('Agent Initialized...')


    def log(self, message: str, level: int = logging.INFO) -> None:
        """
        Records an agents activity or event.

        Args:
            message: Description of the event to be logged.
            level: Logging severity level. Defaults to logging.INFO.
        """

        self.logger.log(level, f"[{self.name}] {message}")

