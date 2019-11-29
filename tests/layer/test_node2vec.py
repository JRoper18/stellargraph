# -*- coding: utf-8 -*-
#
# Copyright 2018 Data61, CSIRO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Node2Vec tests

"""
from stellargraph.core.graph import StellarGraph
from stellargraph.mapper import Node2VecNodeGenerator
from stellargraph.layer.node2vec import *

from tensorflow import keras
import numpy as np
import networkx as nx
import pytest


def example_graph_1(feature_size=None):
    G = nx.Graph()
    elist = [(1, 2), (2, 3), (1, 4), (3, 2)]
    G.add_nodes_from([1, 2, 3, 4], label="default")
    G.add_edges_from(elist, label="default")

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.nodes[v]["feature"] = np.ones(feature_size)
        return StellarGraph(G, node_features="feature")

    else:
        return StellarGraph(G)


def test_node2vec_constructor():
    node2vec = Node2Vec(
        emb_size=4, node_num=4, multiplicity=2
    )
    assert node2vec.emb_size == 4
    assert node2vec.input_node_num == 4
    assert node2vec.multiplicity == 2


    # Check requirement for generator or node_num & multiplicity
    with pytest.raises(KeyError):
        Node2Vec(emb_size=4)

    # Construction from generator
    G = example_graph_1()
    gen = Node2VecNodeGenerator(G, batch_size=2)
    node2vec = Node2Vec(emb_size=4, generator=gen)

    assert node2vec.emb_size == 4
    assert node2vec.input_node_num == 4
    assert node2vec.multiplicity == 1


def test_node2vec_apply():
    node2vec = Node2Vec(
        emb_size=4,
        node_num=4,
        multiplicity=2,
    )

    x = np.array([[1]])
    expected = np.array([[1, 1, 1, 1]])

    inp = keras.Input(shape=(1,))
    out = node2vec(inp)
    model1 = keras.Model(inputs=inp, outputs=out)
    model_weights1 = [np.ones_like(w) for w in model1.get_weights()]
    model1.set_weights(model_weights1)
    actual = model1.predict(x)
    assert expected == pytest.approx(actual)

    # Use the node model:
    xinp, xout = node2vec.node_model()
    model2 = keras.Model(inputs=xinp, outputs=xout)
    model_weights2 = [np.ones_like(w) for w in model2.get_weights()]
    model2.set_weights(model_weights2)
    assert pytest.approx(expected) == model2.predict(x)

    x1 = np.array([[0]])
    x2 = np.array([[2]])
    y1 = np.array([[1, 1, 1, 1]])
    y2 = np.array([[1, 1, 1, 1]])

    # Test the build function:
    xinp, xout = node2vec.build()
    model3 = keras.Model(inputs=xinp, outputs=xout)
    model_weights3 = [np.ones_like(w) for w in model3.get_weights()]
    model3.set_weights(model_weights3)
    actual = model3.predict([x1, x2])
    assert pytest.approx(y1) == actual[0]
    assert pytest.approx(y2) == actual[1]

    # Use the link model:
    xinp, xout = node2vec.link_model()
    model4 = keras.Model(inputs=xinp, outputs=xout)
    model_weights4 = [np.ones_like(w) for w in model4.get_weights()]
    model4.set_weights(model_weights4)
    actual = model4.predict([x1, x2])
    assert pytest.approx(y1) == actual[0]
    assert pytest.approx(y2) == actual[1]


def test_node2vec_serialize():
    node2vec = Node2Vec(
        emb_size=4,
        node_num=4,
        multiplicity=2,
    )

    inp = keras.Input(shape=(1,))
    out = node2vec(inp)
    model = keras.Model(inputs=inp, outputs=out)

    # Save model
    model_json = model.to_json()

    # Set all weights to one
    model_weights = [np.ones_like(w) for w in model.get_weights()]

    # Load model from json & set all weights
    model2 = keras.models.model_from_json(model_json)
    model2.set_weights(model_weights)

    # Test loaded model
    x = np.array([[2]])
    expected = np.array([[1, 1, 1, 1]])

    actual = model2.predict(x)
    assert expected == pytest.approx(actual)