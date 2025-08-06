# 1. Create AI Founddry project in Azure AI Foundry in either SwedenCentral or WestUS region
# 2. Ensure you deployed both o3-deep-research and 4o in same region as the project
# 3. Deoploy BingSearchGrounding in Azure portal, regions not matter
# 4. Update .env file with the following variables:
#    - PROJECT_ENDPOINT: The endpoint of your AI Foundry project
#    - BING_RESOURCE_NAME: The name of your Bing Search Grounding resource
#    - DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME: The deployment name of your o3-deep-research model
#    - MODEL_DEPLOYMENT_NAME: The deployment name of your 4o model
# 5. Run pip install --pre azure-ai-projects, must be pre-release version
# 6. Run pip install azure-ai-projects azure-identity azure-ai-agents
# 7. Ensure Azure Login 

import os, time
from typing import Optional
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import DeepResearchTool, MessageRole, ThreadMessage

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

def fetch_and_print_new_agent_response(
    thread_id: str,
    agents_client: AgentsClient,
    last_message_id: Optional[str] = None,
) -> Optional[str]:
    response = agents_client.messages.get_last_message_by_role(
        thread_id=thread_id,
        role=MessageRole.AGENT,
    )
    if not response or response.id == last_message_id:
        return last_message_id, None  # No new content

    print("\nAgent response:")
    print("\n".join(t.text.value for t in response.text_messages))

    for ann in response.url_citation_annotations:
        print(f"URL Citation: [{ann.url_citation.title}]({ann.url_citation.url})")

    return response.id, response


def create_research_summary(
        message : ThreadMessage,
        filepath: str = "research_summary.md"
) -> None:
    if not message:
        print("No message content provided, cannot create research summary.")
        return

    with open(filepath, "w", encoding="utf-8") as fp:
        # Write text summary
        text_summary = "\n\n".join([t.text.value.strip() for t in message.text_messages])
        fp.write(text_summary)

        # Write unique URL citations, if present
        if message.url_citation_annotations:
            fp.write("\n\n## References\n")
            seen_urls = set()
            for ann in message.url_citation_annotations:
                url = ann.url_citation.url
                title = ann.url_citation.title or url
                if url not in seen_urls:
                    fp.write(f"- [{title}]({url})\n")
                    seen_urls.add(url)

    print(f"Research summary written to '{filepath}'.")

print(os.getenv("PROJECT_ENDPOINT")),

project_client = AIProjectClient(
    endpoint=os.getenv("PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential(),
)

conn_id = project_client.connections.get(name=os.getenv("BING_RESOURCE_NAME")).id


# Initialize a Deep Research tool with Bing Connection ID and Deep Research model deployment name
deep_research_tool = DeepResearchTool(
    bing_grounding_connection_id=conn_id,
    deep_research_model=os.getenv("DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME"),
)

# Create Agent with the Deep Research tool and process Agent run
with project_client:

    with project_client.agents as agents_client:

        # Create a new agent that has the Deep Research tool attached.
        agent = agents_client.create_agent(
            model=os.getenv("MODEL_DEPLOYMENT_NAME"),
            name="deep-research-agent",
            instructions="You are a helpful Agent that assists in researching scientific topics.",
            tools=deep_research_tool.definitions,
        )
        print(f"Created agent, ID: {agent.id}")

        # Create thread for communication
        thread = agents_client.threads.create()
        print(f"Created thread, ID: {thread.id}")

        # user_content = "Research data regarding the investment in renewable energy, energy capacity, and energy consumption of countries in Sub-Saharan Africa"
        user_content = "分析美国加息政策对全球高等教育的影响，特别是对中国留学生的影响。请提供相关数据和研究结果。结果以简单中文输出。"
        last_message_id = None
        while True:
            message = agents_client.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_content,
            )
            print(f"Created message, ID: {message.id}")

            print("Start processing the message... this may take a few minutes to finish. Be patient!")
            run = agents_client.runs.create(thread_id=thread.id, agent_id=agent.id)
            agent_response = None
            while run.status in ("queued", "in_progress"):
                time.sleep(1)
                run = agents_client.runs.get(thread_id=thread.id, run_id=run.id)
                last_message_id, agent_response = fetch_and_print_new_agent_response(
                    thread_id=thread.id,
                    agents_client=agents_client,
                    last_message_id=last_message_id,
                )
                print(f"Run status: {run.status}")

            print(f"Run finished with status: {run.status}, ID: {run.id}")

            if run.status == "failed":
                print(f"Run failed: {run.last_error}")
                break

            # let customer decide whether to add more content or finish the research summary
            if agent_response:
                user_decision = input("Any supplementaries? (y/n，n will finish and compose final deliverables)：").strip().lower()
                if user_decision == "y":
                    user_content = input("Supplementary content: ")
                    continue
                else:
                    create_research_summary(agent_response)
                    break

        # Clean-up and delete the agent once the run is finished.
        # NOTE: Comment out this line if you plan to reuse the agent later.
        # agents_client.delete_agent(agent.id)
        # print("Deleted agent")


