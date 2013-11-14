from wheelcms_axle.node import Node

import pytest

@pytest.fixture
def root():
    return Node.root()
