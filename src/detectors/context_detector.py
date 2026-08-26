# Thin wrapper around the vectorstore's retrieve_context().
from knowledge.vectorstore import retrieve_context

def get_enterprise_context(prompt):

    context = retrieve_context(prompt)

    print("Retrieved context:", context) #remove before sending to prod.

    return context