__version__ = '0.2.1'

#
#    Copyright (C) 2018 by
#    Thomas Bonald <thomas.bonald@telecom-paristech.fr>
#    Bertrand Charpentier <bertrand.charpentier@live.fr>
#    All rights reserved.
#    BSD license.

#    source: https://github.com/tbonald/paris/blob/master/paris.py
#    theory: https://arxiv.org/pdf/1806.01664.pdf
#    this is a slighly modified version of paris, dubbed "krakow"

import numpy as np
import networkx as nx


def krakow(G, alpha=2, beta=2, copy_graph=True):
    """
    alpha and beta should be >= 1
    at alpha==beta==1, the algorithm is the same as paris
    the higher those paramters, the more even the merges
    but too high values can harm clustering quality
    """
    assert alpha >= 1
    assert beta >= 1

    n = G.number_of_nodes()
    if copy_graph:
        F = G.copy()
    else:
        F = G

    # index nodes from 0 to n - 1
    if set(F.nodes()) != set(range(n)):
        F = nx.convert_node_labels_to_integers(F)

    # node weights
    w = {u: 0 for u in range(n)}
    wtot = 0
    for (u, v) in F.edges():
        if "weight" not in F[u][v]:
            F[u][v]["weight"] = 1
        weight = F[u][v]["weight"]
        w[u] += weight
        w[v] += weight
        wtot += weight
        if u != v:
            wtot += weight

    # cluster sizes
    s = {u: 1 for u in range(n)}

    # connected components
    cc = []

    # dendrogram as list of merges
    D = []

    # cluster index
    u = n
    while n > 0:
        # nearest-neighbor chain
        chain = [list(F.nodes())[0]]
        while chain != []:
            a = chain.pop()
            # nearest neighbor
            dmin = float("inf")
            b = -1
            for v in F.neighbors(a):
                if v != a:
                    small = min(w[v], w[a])
                    big = max(w[v], w[a])
                    d = (
                        (small ** alpha) * (big ** beta)
                        / float(F[a][v]["weight"])
                        / float(wtot)
                    )
                    # d = w[v] * w[a] / float(F[a][v]['weight']) / float(wtot)
                    if d < dmin:
                        b = v
                        dmin = d
                    elif d == dmin:
                        b = min(b, v)
            d = dmin
            if chain != []:
                c = chain.pop()
                if b == c:
                    # merge a,b
                    D.append([a, b, d, s[a] + s[b]])
                    # update graph
                    F.add_node(u)
                    neighbors_a = list(F.neighbors(a))
                    neighbors_b = list(F.neighbors(b))
                    for v in neighbors_a:
                        F.add_edge(u, v, weight=F[a][v]["weight"])
                    for v in neighbors_b:
                        if F.has_edge(u, v):
                            F[u][v]["weight"] += F[b][v]["weight"]
                        else:
                            F.add_edge(u, v, weight=F[b][v]["weight"])
                    F.remove_node(a)
                    F.remove_node(b)
                    n -= 1
                    # update weight and size
                    w[u] = w.pop(a) + w.pop(b)
                    s[u] = s.pop(a) + s.pop(b)
                    # change cluster index
                    u += 1
                else:
                    chain.append(c)
                    chain.append(a)
                    chain.append(b)
            elif b >= 0:
                chain.append(a)
                chain.append(b)
            else:
                # remove the connected component
                cc.append((a, s[a]))
                F.remove_node(a)
                w.pop(a)
                s.pop(a)
                n -= 1

    # add connected components to the dendrogram
    a, s = cc.pop()
    for b, t in cc:
        s += t
        D.append([a, b, float("inf"), s])
        a = u
        u += 1

    return reorder_dendrogram(np.array(D))


def reorder_dendrogram(D):
    n = np.shape(D)[0] + 1
    order = np.zeros((2, n - 1), float)
    order[0] = range(n - 1)
    order[1] = np.array(D)[:, 2]
    index = np.lexsort(order)
    nindex = {i: i for i in range(n)}
    nindex.update({n + index[t]: n + t for t in range(n - 1)})
    return np.array(
        [
            [nindex[int(D[t][0])], nindex[int(D[t][1])], D[t][2], D[t][3]]
            for t in range(n - 1)
        ]
    )[index, :]
