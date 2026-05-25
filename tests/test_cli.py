from pathlib import Path

EXAMPLES = Path(__file__).parent.parent / "examples"
FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_slr_arithmetic_exits_zero(capsys):
    from yapar.__main__ import main

    rc = main([str(EXAMPLES / "arithmetic.yalp")])
    assert rc == 0
    captured = capsys.readouterr()
    assert "SLR(1)" in captured.out


def test_cli_lalr_arithmetic_exits_zero(capsys):
    from yapar.__main__ import main

    rc = main([str(EXAMPLES / "arithmetic.yalp"), "--method", "lalr"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "LALR(1)" in captured.out


def test_cli_conflict_grammar_exits_one(capsys):
    from yapar.__main__ import main

    rc = main([str(EXAMPLES / "conflict_demo.yalp")])
    assert rc == 1
    captured = capsys.readouterr()
    assert "conflict" in captured.err


def test_cli_table_flag_shows_acc(capsys):
    from yapar.__main__ import main

    rc = main([str(FIXTURES / "simple.yalp"), "--table"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "acc" in captured.out


def test_cli_validation_catches_undefined_symbol(capsys, tmp_path):
    bad = tmp_path / "bad.yalp"
    bad.write_text("TOKENS ID\n%%\nS : GHOST ;\n", encoding="utf-8")

    from yapar.__main__ import main

    rc = main([str(bad)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "GHOST" in captured.err


def test_cli_no_validate_skips_check(tmp_path):
    bad = tmp_path / "bad.yalp"
    bad.write_text("TOKENS ID GHOST\n%%\nS : GHOST ;\n", encoding="utf-8")

    from yapar.__main__ import main

    rc = main([str(bad), "--no-validate"])
    assert rc == 0


def test_cli_render_dot(capsys, tmp_path):
    from yapar.__main__ import main

    out = tmp_path / "automaton.dot"
    rc = main([str(FIXTURES / "simple.yalp"), "--render", str(out)])
    assert rc == 0
    assert out.exists()
    captured = capsys.readouterr()
    assert "automaton" in captured.out


def test_cli_parse_valid_input(tmp_path, capsys):
    tokens_file = tmp_path / "tokens.tsv"
    tokens_file.write_text("ID\tx\t1\t1\n$\t$\t-1\t-1\n", encoding="utf-8")

    from yapar.__main__ import main

    rc = main([str(FIXTURES / "simple.yalp"), str(tokens_file)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "OK" in captured.out


def test_cli_parse_invalid_input_exits_one(tmp_path, capsys):
    tokens_file = tmp_path / "tokens.tsv"
    tokens_file.write_text("PLUS\t+\t1\t1\n$\t$\t-1\t-1\n", encoding="utf-8")

    from yapar.__main__ import main

    rc = main([str(FIXTURES / "simple.yalp"), str(tokens_file)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "parse error" in captured.err


def test_cli_lalr_parses_arithmetic_expression(tmp_path, capsys):
    tokens_file = tmp_path / "tokens.tsv"
    tokens_file.write_text(
        "ID\ta\t1\t1\nPLUS\t+\t1\t2\nID\tb\t1\t3\n$\t$\t-1\t-1\n",
        encoding="utf-8",
    )

    from yapar.__main__ import main

    rc = main(
        [str(FIXTURES / "simple.yalp"), str(tokens_file), "--method", "lalr"]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "OK" in captured.out
