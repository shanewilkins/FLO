import io
import sys

from flo.services.io import read_input, write_output
from flo.services.errors import EXIT_RENDER_ERROR


def test_read_input_file(tmp_path):
    p = tmp_path / "sample.flo"
    p.write_text("hello world", encoding="utf-8")
    rc, content, err = read_input(str(p))
    assert rc == 0
    assert content == "hello world"
    assert err == ""


def test_read_input_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("stdin content"))
    rc, content, err = read_input("-")
    assert rc == 0
    assert content == "stdin content"


def test_read_input_missing_file():
    rc, content, err = read_input("/this/path/does/not/exist.flo")
    assert rc == EXIT_RENDER_ERROR
    assert content == ""
    assert "I/O error reading" in err


def test_write_output_file(tmp_path):
    out_path = tmp_path / "out.txt"
    rc, err = write_output("payload", str(out_path))
    assert rc == 0
    assert err == ""
    assert out_path.read_text(encoding="utf-8") == "payload"


def test_write_output_stdout(capsys):
    rc, err = write_output("hello-stdout", None)
    captured = capsys.readouterr()
    assert rc == 0
    assert err == ""
    assert "hello-stdout" in captured.out


def test_write_output_oserror(monkeypatch):
    import builtins

    def fake_open(*args, **kwargs):
        raise OSError("no space")

    monkeypatch.setattr(builtins, "open", fake_open)
    rc, err = write_output("payload", "somepath")
    assert rc == EXIT_RENDER_ERROR
    assert "I/O error writing" in err
