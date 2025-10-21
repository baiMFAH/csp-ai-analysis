from airbnb_identity import GoogleIapCredential
from openai import AzureOpenAI

# This is the URL that's used for calls from your laptop or airdev workspaces
# See the other example for calls from a service or CI
endpoint = "https://devaigateway.a.musta.ch"

# Get an auth token (will spawn a browser window if you're not already logged in)
auth = GoogleIapCredential().authenticate(endpoint)

# See the list of available models at https://devaigateway.a.musta.ch/v1/models
# And contact #ai-for-dev-productivity for current recommendations for your usage case
# ('best_coding' aliases to the strongest current model for coding)
#model_name = "best_coding"
model_name = "gpt-4o"

# Note: With DevAIGateway, you should always use AzureOpenAI regardless of the model
# (even models not from OpenAI)
client = AzureOpenAI(
  azure_endpoint=endpoint,
  api_version="2025-01-01-preview",
  azure_ad_token=auth.headers["Authorization"].split()[-1]
)

prompt_messages = [
    {
        "role": "user",
        "content": "Quick, what's a really cool idea for a new internal coding tool at Airbnb that uses AI?",
    }
]

# Create the chat completion
response = client.chat.completions.create(
    model=model_name,
    messages=prompt_messages,
)

# Print the response
print(response.choices[0].message.content)