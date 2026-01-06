"""Tests für Shell-Sicherheitsschicht."""

import pytest

from code.tools.shell import check_command_safety, shell_exec


class TestBlockedPatterns:
    """Tests für gefährliche Befehle."""

    def test_rm_rf_root_blocked(self):
        """rm -rf / wird geblockt."""
        is_safe, msg = check_command_safety("rm -rf /")
        assert not is_safe
        assert "Blocked" in msg

    def test_rm_rf_double_slash_blocked(self):
        """rm -rf // wird geblockt."""
        is_safe, msg = check_command_safety("rm -rf //")
        assert not is_safe
        assert "Blocked" in msg

    def test_rm_rf_dot_slash_blocked(self):
        """rm -rf /./ wird geblockt."""
        is_safe, msg = check_command_safety("rm -rf /./")
        assert not is_safe
        assert "Blocked" in msg

    def test_rm_rf_home_blocked(self):
        """rm -rf ~ wird geblockt."""
        is_safe, msg = check_command_safety("rm -rf ~")
        assert not is_safe
        assert "Blocked" in msg

    def test_rm_rf_star_blocked(self):
        """rm -rf * wird geblockt."""
        is_safe, msg = check_command_safety("rm -rf *")
        assert not is_safe
        assert "Blocked" in msg

    def test_dd_dev_blocked(self):
        """dd auf /dev/ wird geblockt."""
        is_safe, msg = check_command_safety("dd if=/dev/zero of=/dev/sda")
        assert not is_safe
        assert "Blocked" in msg

    def test_dd_of_dev_only_blocked(self):
        """dd of=/dev/sda (ohne if=) wird geblockt."""
        is_safe, msg = check_command_safety("dd of=/dev/sda bs=1M")
        assert not is_safe
        assert "Blocked" in msg

    def test_mkfs_blocked(self):
        """mkfs wird geblockt."""
        is_safe, msg = check_command_safety("mkfs.ext4 /dev/sda1")
        assert not is_safe
        assert "Blocked" in msg

    def test_chmod_777_root_blocked(self):
        """chmod 777 / wird geblockt."""
        is_safe, msg = check_command_safety("chmod 777 /")
        assert not is_safe
        assert "Blocked" in msg

    def test_chmod_R_777_etc_blocked(self):
        """chmod -R 777 /etc wird geblockt."""
        is_safe, msg = check_command_safety("chmod -R 777 /etc")
        assert not is_safe
        assert "Blocked" in msg

    def test_redirect_dev_blocked(self):
        """> /dev/sda wird geblockt."""
        is_safe, msg = check_command_safety("echo x > /dev/sda")
        assert not is_safe
        assert "Blocked" in msg

    def test_cat_redirect_dev_blocked(self):
        """cat > /dev/sda wird geblockt."""
        is_safe, msg = check_command_safety("cat file.txt > /dev/sda")
        assert not is_safe
        assert "Blocked" in msg

    def test_tee_dev_blocked(self):
        """tee /dev/sda wird geblockt."""
        is_safe, msg = check_command_safety("echo x | tee /dev/sda")
        assert not is_safe
        assert "Blocked" in msg

    def test_pipe_dd_dev_blocked(self):
        """Pipe zu dd of=/dev wird geblockt."""
        is_safe, msg = check_command_safety("cat image.iso | dd of=/dev/sda")
        assert not is_safe
        assert "Blocked" in msg


class TestSafeCommands:
    """Tests für erlaubte Befehle."""

    def test_ls_allowed(self):
        """ls -la geht durch."""
        is_safe, msg = check_command_safety("ls -la")
        assert is_safe
        assert msg == ""

    def test_rm_file_allowed(self):
        """rm auf einzelne Datei erlaubt."""
        is_safe, msg = check_command_safety("rm /tmp/testfile.txt")
        assert is_safe

    def test_cat_allowed(self):
        """cat erlaubt."""
        is_safe, msg = check_command_safety("cat /etc/passwd")
        assert is_safe


class TestSudoWarning:
    """Tests für Sudo-Warnung."""

    def test_sudo_warning(self):
        """sudo apt update gibt Warnung."""
        is_safe, msg = check_command_safety("sudo apt update")
        assert not is_safe
        assert "Sudo" in msg

    def test_sudo_with_spaces(self):
        """sudo mit Leerzeichen davor."""
        is_safe, msg = check_command_safety("  sudo reboot")
        assert not is_safe
        assert "Sudo" in msg


class TestShellExecIntegration:
    """Integration Tests für shell_exec."""

    @pytest.mark.asyncio
    async def test_blocked_command_not_executed(self):
        """Geblockte Befehle werden nicht ausgeführt."""
        result = await shell_exec(command="rm -rf /")
        assert "Blocked" in result

    @pytest.mark.asyncio
    async def test_safe_command_executed(self):
        """Sichere Befehle werden ausgeführt."""
        result = await shell_exec(command="echo test")
        assert "test" in result
