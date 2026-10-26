## A Juicy Commercial Problem: The Price Is Right.
Given a description of a product, predict its price. 

1. The true value of a product
2. This will ultimately be incorporated in an Agentic Solution that will hunt for bargains

We will build an Autonomous Agentic AI framework
    - watches for deals being published online
    - estimates the price of the product
    - sends a push notification when it finds great opportunities

Seven Agents will collaborate in our framework:
    - GPT-5 model will identify the deals from an RSS feed
    - Our frontier-busting fine-tuned model will estimate prices
    - We'll also use a frontier model with a massive RAG db


### Agent Architecture
1. Scanner Agent - identifies promising deals
2. Emsemble Agent - estimates prices using multiple models
3. Messaging Agent - sends push notification
4. Planning Agent - coordinates activities
5. The Agent Framework - with memory and logging
6. The UI - use gradio

Modal - deploy the LLM model for making inference

### How will we evaluate performance?
1. Model-centric or Technical Metrics - Loss
2. Business-centric or Outcome Metrics - Actual difference in Price





