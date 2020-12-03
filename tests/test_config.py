from gemeaux import Config


def test_default_config():
    config = Config()
    assert config.ip == "localhost"
    assert config.port == 1965
    assert config.certfile == "cert.pem"
    assert config.keyfile == "key.pem"
    assert config.nb_connections == 5
