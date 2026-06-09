from collections import defaultdict

from langchain_core.documents import Document


# Raw Documents to Langchain Documents
def get_langchain_docs(docs:str):
    lc_docs = []
    for doc in docs:
        document = Document(
            page_content=doc['content'],
            metadata=doc['metadata']
        )
        lc_docs.append(document)
    return lc_docs



docs = {
    1: "Artificial intelligence and machine learning are transforming modern software systems by enabling automated decision making and intelligent data analysis.",
    2: "Smart parking systems use sensors, real time data processing, and predictive analytics to efficiently allocate parking slots and reduce traffic congestion in urban cities.",
    3: "Data science combines statistics, programming, and domain knowledge to extract meaningful insights from large datasets for business and research applications."
}


index = defaultdict(set)
for doc_id, text in docs.items():
    words = text.lower().split()
    for word in words:
        index[word].add(doc_id)


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

def autocomplete(prefix):
    results = []
    trie = Trie()
    for text in docs.values():
        for word in text.split():
             trie.insert(word)

    def dfs(node, path):
        if node.is_end:
            results.append(path)
        for ch, nxt in node.children.items():
            dfs(nxt, path + ch)

    node = trie.root
    for ch in prefix:
        if ch not in node.children:
            return []
        node = node.children[ch]

    dfs(node, prefix)
    return results

def auto_complete(query):
    result = []

    for q in query.split():
        try:
            result.append(autocomplete(q)[0])
        except IndexError:
            continue

    return " ".join(result)

def ranked_search(query):
    words = query.lower().split()
    score = {}

    for w in words:
        for doc in index[w]:
            score[doc] = score.get(doc, 0) + 1

    return sorted(score.items(), key=lambda x: x[1], reverse=True)

def get_doc(query):
    ranked = ranked_search(query)
    docs = []
    if len(ranked)>0:
        for i in range(len(ranked)):
            docs.append(ranked[i][0])
    return docs[:2]
  
query = "Smar par system combines  Data science statistics"  
def final_docs_Search(query):
    sent = auto_complete(query)
    result = get_doc(sent)
    return result

print(final_docs_Search(query))