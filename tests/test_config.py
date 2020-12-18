from unittest.mock import patch

from gemeaux import ArgsConfig, ZeroConfig


def test_zero_config():
    config = ZeroConfig()
    assert config.ip == "localhost"
    assert config.port == 1965
    assert config.certfile == "cert.pem"
    assert config.keyfile == "key.pem"
    assert config.nb_connections == 5


def test_args_config():
    testargs = ["prog"]
    with patch("sys.argv", testargs):
        config = ArgsConfig()
    assert config.ip == "localhost"
    assert config.port == 1965
    assert config.certfile == "cert.pem"
    assert config.keyfile == "key.pem"
    assert config.nb_connections == 5
