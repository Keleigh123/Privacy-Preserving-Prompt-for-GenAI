from ollama import chat
from knowledge.vectorstore import retrieve_context

def contextual_analysis(prompt):
    context = retrieve_context(prompt)

    context_text = "\n".join(context)


    response = chat(
        model="llama3.2",
        messages=[
        {
            "role":"system",
            "content":f"""
            You are a privacy detector.

            Enterprise Context:
{context_text}

Analyse the user prompt.

Determine whether the prompt contains:

- Confidential projects
- Customer information
- Internal organisational data
- Sensitive business information

            Return:

            Risk Score: 0-100

            Explain why.
            """
        },
        {
            "role":"user",
            "content":prompt
        }]
    )

    return response["message"]["content"]