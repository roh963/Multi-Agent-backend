from agent import search_search_agent, build_reader_agent, writer_chain, critic_chain

def run_research_pipeline(topic: str):
    state ={}

    # Step 1: Search for working
    print("\n" + "="*20 + " Step 1: Searching for wroking" + "="*20 + "\n")
    search_agent = search_search_agent()
    search_results = search_agent.invoke(
        {
            "messages": [("user", f"Find the recent and reliable information on the topic: {topic}")]
        }
    )

    state["search_results"] = search_results["messages"][-1].content
    print(f"Search Results:\n{state['search_results']}\n")

    # Step 2: Read and extract insights
    print("\n" + "="*20 + " Step 2: Extracting insights using scraping" + "="*20 + "\n")
    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user", 
            f"Based on the following search results, extract key insights and relevant information for the topic: {topic}"
            f"pick the most relevant URLs and scrape it for deep content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
            )]
    })

    state["scraped_content"] = reader_result["messages"][-1].content
    print(f"Extracted Information:\n{state['scraped_content']}\n")
    # Step 3: Write a structured report
    print("\n" + "="*20 + " Step 3: Writing a structured report" + "="*20 + "\n")

    research_combined  = (f"Search Results:\n{state['search_results']}\n\n"
                          f"Detailed Scraped Content:\n{state['scraped_content']}\n")

    state["report"]= writer_chain.invoke({"topic": topic, "research": research_combined})

    print("\n" + "="*20 + " Final Report " + "="*20 + "\n")
    print(state["report"])
    
    # Step 4: Critique the report
    print("\n" + "="*20 + " Step 4: Critiquing the report" + "="*20 + "\n")
    state["feedback"] = critic_chain.invoke({"report": state["report"]})

 
    print("\n" + "="*20 + " Critique " + "="*20 + "\n")
    print(state["feedback"])

    
    return state


# if __name__ == "__main__":
#     topic = input("Enter a research topic: ")
#     run_research_pipeline(topic)