from knowledge.vectorstore import retrieve_context

def get_enterprise_context(prompt):

    context = retrieve_context(prompt)

    print("Retrieved context:", context)

    return context