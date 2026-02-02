"""Tests for CLI dispatcher."""

import sys
import pytest
from unittest.mock import patch, MagicMock
from ofs.cli.dispatcher import main

class TestDispatcher:
    """Tests for CLI dispatcher main function."""

    def test_no_args_prints_help(self, capsys):
        """No arguments prints help."""
        with patch.object(sys, 'argv', ['ofs']):
            assert main() == 0
        captured = capsys.readouterr()
        assert "usage: ofs" in captured.out

    def test_init_command(self):
        """Init command dispatches correctly."""
        with patch.object(sys, 'argv', ['ofs', 'init']):
            with patch('ofs.core.repository.init.Repository') as MockRepo:
                instance = MockRepo.return_value
                instance.initialize.return_value = True
                assert main() == 0
                instance.initialize.assert_called_once()

    def test_add_command(self):
        """Add command dispatches to execute."""
        with patch.object(sys, 'argv', ['ofs', 'add', 'file.txt']):
            with patch('ofs.commands.add.execute', return_value=0) as mock_add:
                assert main() == 0
                mock_add.assert_called_with(['file.txt'])

    def test_commit_command(self):
        """Commit command dispatches."""
        with patch.object(sys, 'argv', ['ofs', 'commit', '-m', 'msg']):
            with patch('ofs.commands.commit.execute', return_value=0) as mock_commit:
                assert main() == 0
                mock_commit.assert_called_with('msg')

    def test_verify_command(self):
        """Verify command dispatches."""
        with patch.object(sys, 'argv', ['ofs', 'verify', '--verbose']):
            with patch('ofs.commands.verify.execute', return_value=0) as mock_verify:
                assert main() == 0
                mock_verify.assert_called_with(verbose=True)

    def test_checkout_command(self):
        """Checkout command dispatches."""
        with patch.object(sys, 'argv', ['ofs', 'checkout', 'HEAD', '--force']):
            with patch('ofs.commands.checkout.execute', return_value=0) as mock_checkout:
                assert main() == 0
                mock_checkout.assert_called_with('HEAD', force=True)

    def test_exception_handling(self, capsys):
        """Exceptions are caught and printed."""
        with patch.object(sys, 'argv', ['ofs', 'init']):
            with patch('ofs.core.repository.init.Repository', side_effect=Exception("Boom")):
                assert main() == 1
        captured = capsys.readouterr()
        assert "Error: Boom" in captured.out

    def test_unknown_command_via_argparse(self):
        """Argparse handles unknown commands (exits)."""
        # Argparse usually calls sys.exit(2) on error
        with patch.object(sys, 'argv', ['ofs', 'unknown']), pytest.raises(SystemExit):
            main()
