import json
from src.core import Connector, prettyPrint, logInit
from src.model import Issue, PeppermintButler


if __name__ == "__main__" :
    logInit()
    jira = Connector()

    butler = PeppermintButler(jira)
    i = butler.giveMeTask()
