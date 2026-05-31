"""Unit tests for Config."""

import json
import time

import pytest

from src.config import Config, ConfigError, Environment


class TestConfigDefaults:
    def test_default_environment_is_prod(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.environment == Environment.PROD

    def test_default_debug_is_false(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.debug is False

    def test_default_is_not_dev(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.environment != Environment.DEV

    def test_default_is_not_test(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.environment != Environment.TEST


class TestConfigLoad:
    def test_loads_environment_from_file(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "dev"}))
        assert Config(config_path=path).environment == Environment.DEV

    def test_loads_debug_true_from_file(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"debug": True}))
        assert Config(config_path=path).debug is True

    def test_missing_file_uses_defaults(self, tmp_path):
        config = Config(config_path=tmp_path / "nonexistent.json")
        assert config.environment == Environment.PROD

    def test_get_custom_key(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"my_setting": 42}))
        assert Config(config_path=path).get("my_setting") == 42

    def test_get_missing_key_returns_default(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get("missing", "fallback") == "fallback"

    def test_loads_all_environments(self, tmp_path):
        for env in ("dev", "test", "prod", "prototype"):
            path = tmp_path / f"config_{env}.json"
            path.write_text(json.dumps({"environment": env}))
            assert Config(config_path=path).environment == Environment(env)


class TestConfigEnvironmentVariableOverrides:
    def test_tick_tock_env_sets_dev(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_ENV", "dev")
        assert Config(config_path=tmp_path / "c.json").environment == Environment.DEV

    def test_tick_tock_env_sets_test(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_ENV", "test")
        assert Config(config_path=tmp_path / "c.json").environment == Environment.TEST

    def test_tick_tock_debug_true(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_DEBUG", "true")
        assert Config(config_path=tmp_path / "c.json").debug is True

    def test_tick_tock_debug_1(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_DEBUG", "1")
        assert Config(config_path=tmp_path / "c.json").debug is True

    def test_tick_tock_debug_yes(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_DEBUG", "yes")
        assert Config(config_path=tmp_path / "c.json").debug is True

    def test_tick_tock_debug_false_string(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_DEBUG", "false")
        assert Config(config_path=tmp_path / "c.json").debug is False

    def test_env_var_overrides_file_value(self, tmp_path, monkeypatch):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "test"}))
        monkeypatch.setenv("TICK_TOCK_ENV", "dev")
        assert Config(config_path=path).environment == Environment.DEV

    def test_invalid_env_var_value_falls_back_to_prod(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_ENV", "not_a_real_env")
        assert Config(config_path=tmp_path / "c.json").environment == Environment.PROD


class TestConfigSet:
    def test_set_changes_value(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.set("environment", "dev")
        assert config.environment == Environment.DEV

    def test_set_custom_key(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.set("my_key", "my_value")
        assert config.get("my_key") == "my_value"


class TestConfigSave:
    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "config.json"
        config = Config(config_path=path)
        config.save()
        assert path.exists()

    def test_saved_file_is_valid_json(self, tmp_path):
        path = tmp_path / "config.json"
        config = Config(config_path=path)
        config.save()
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_save_persists_set_value(self, tmp_path):
        path = tmp_path / "config.json"
        config = Config(config_path=path)
        config.set("environment", "dev")
        config.save()
        config2 = Config(config_path=path)
        assert config2.environment == Environment.DEV

    def test_save_creates_parent_directory(self, tmp_path):
        path = tmp_path / "subdir" / "config.json"
        config = Config(config_path=path)
        config.save()
        assert path.exists()

    def test_save_no_tmp_file_left_behind(self, tmp_path):
        path = tmp_path / "config.json"
        config = Config(config_path=path)
        config.save()
        assert not (tmp_path / "config.tmp").exists()

    def test_save_raises_config_error_on_bad_path(self, tmp_path):
        # Use a path whose parent is actually a file, so mkdir fails.
        blocker = tmp_path / "blocker"
        blocker.write_text("x")
        path = blocker / "config.json"
        config = Config.__new__(Config)
        config._config = Config.DEFAULT_CONFIG.copy()
        config._config_path = path
        config._last_mtime = None
        with pytest.raises(ConfigError):
            config.save()


# ------------------------------------------------------------------
# v0.0.2 - Auto-creation
# ------------------------------------------------------------------


class TestConfigAutoCreation:
    def test_missing_file_is_created_on_init(self, tmp_path):
        path = tmp_path / "config.json"
        assert not path.exists()
        Config(config_path=path)
        assert path.exists()

    def test_auto_created_file_contains_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        Config(config_path=path)
        data = json.loads(path.read_text())
        assert data["environment"] == "prod"
        assert data["debug"] is False

    def test_existing_file_is_not_overwritten(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "dev", "debug": True}))
        Config(config_path=path)
        data = json.loads(path.read_text())
        assert data["environment"] == "dev"

    def test_auto_create_in_nested_directory(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "config.json"
        Config(config_path=path)
        assert path.exists()


# ------------------------------------------------------------------
# v0.0.2 - Safe load with error handling
# ------------------------------------------------------------------


class TestConfigSafeLoad:
    def test_malformed_json_uses_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("{ this is not json }")
        config = Config(config_path=path)
        assert config.environment == Environment.PROD

    def test_malformed_json_sets_load_error(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("{ bad json }")
        config = Config(config_path=path)
        assert config.load_error is not None

    def test_clean_load_has_no_error(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "dev"}))
        config = Config(config_path=path)
        assert config.load_error is None

    def test_missing_file_has_no_load_error(self, tmp_path):
        config = Config(config_path=tmp_path / "nonexistent.json")
        assert config.load_error is None

    def test_reload_clears_previous_load_error(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("{ bad json }")
        config = Config(config_path=path)
        assert config.load_error is not None
        path.write_text(json.dumps({"environment": "dev"}))
        config.reload()
        assert config.load_error is None

    def test_reload_updates_values(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "prod"}))
        config = Config(config_path=path)
        assert config.environment == Environment.PROD
        path.write_text(json.dumps({"environment": "dev"}))
        config.reload()
        assert config.environment == Environment.DEV

    def test_non_object_json_root_uses_defaults_and_sets_load_error(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps(["not", "an", "object"]))
        config = Config(config_path=path)
        assert config.environment == Environment.PROD
        assert config.load_error is not None


# ------------------------------------------------------------------
# v0.0.2 - Development mode detection
# ------------------------------------------------------------------


class TestConfigDevMode:
    def test_is_prod_true_for_prod(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.environment == Environment.PROD

    def test_is_prod_false_for_dev(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "dev"}))
        assert Config(config_path=path).environment != Environment.PROD

    def test_is_prototype_true(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "prototype"}))
        assert Config(config_path=path).environment == Environment.PROTOTYPE

    def test_is_prototype_false_for_prod(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.environment != Environment.PROTOTYPE

    def test_all_mode_flags_are_mutually_exclusive(self, tmp_path):
        for env in ("dev", "test", "prod", "prototype"):
            path = tmp_path / f"c_{env}.json"
            path.write_text(json.dumps({"environment": env}))
            config = Config(config_path=path)
            flags = [
                config.environment == Environment.DEV,
                config.environment == Environment.TEST,
                config.environment == Environment.PROD,
                config.environment == Environment.PROTOTYPE,
            ]
            assert (
                flags.count(True) == 1
            ), f"expected exactly one True flag for env={env}"


# ------------------------------------------------------------------
# v0.0.2 - Hot-reload
# ------------------------------------------------------------------


class TestConfigHotReload:
    def test_start_watching_sets_is_watching(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.start_watching(interval=0.05)
        assert config._watch_thread is not None and config._watch_thread.is_alive()
        config.stop_watching()

    def test_stop_watching_clears_is_watching(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.start_watching(interval=0.05)
        config.stop_watching()
        assert config._watch_thread is None

    def test_double_start_does_not_spawn_two_threads(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.start_watching(interval=0.05)
        thread1 = config._watch_thread
        config.start_watching(interval=0.05)
        thread2 = config._watch_thread
        assert thread1 is thread2
        config.stop_watching()

    def test_file_change_triggers_callback(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "prod"}))
        config = Config(config_path=path)

        received: list[Config] = []
        config.on_reload(received.append)
        config.start_watching(interval=0.05)

        # Overwrite the file - ensure a distinct mtime by touching the file
        # slightly in the future relative to the last recorded mtime.
        time.sleep(0.1)
        path.write_text(json.dumps({"environment": "dev"}))

        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and not received:
            time.sleep(0.05)

        config.stop_watching()
        assert received, "callback was never called after file change"
        assert config.environment == Environment.DEV

    def test_callback_receives_config_instance(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "prod"}))
        config = Config(config_path=path)

        received: list[Config] = []
        config.on_reload(received.append)
        config.start_watching(interval=0.05)

        time.sleep(0.1)
        path.write_text(json.dumps({"environment": "dev"}))

        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and not received:
            time.sleep(0.05)

        config.stop_watching()
        assert received and received[0] is config

    def test_no_callback_when_file_unchanged(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "prod"}))
        config = Config(config_path=path)

        received: list[Config] = []
        config.on_reload(received.append)
        config.start_watching(interval=0.05)

        time.sleep(0.3)
        config.stop_watching()
        assert not received


# ------------------------------------------------------------------
# v0.6.0 - UI preferences
# ------------------------------------------------------------------


class TestConfigUiPreferences:
    def test_default_always_on_top_is_true(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get_ui_pref("always_on_top") is True

    def test_default_opacity_is_0_90(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get_ui_pref("opacity") == pytest.approx(0.90)

    def test_default_window_x_is_none(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get_ui_pref("window_x") is None

    def test_default_window_y_is_none(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get_ui_pref("window_y") is None

    def test_get_ui_pref_missing_key_returns_default(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get_ui_pref("nonexistent", 42) == 42

    def test_set_ui_pref_updates_value(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.set_ui_pref("always_on_top", False)
        assert config.get_ui_pref("always_on_top") is False

    def test_set_ui_pref_window_position(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.set_ui_pref("window_x", 100)
        config.set_ui_pref("window_y", 200)
        assert config.get_ui_pref("window_x") == 100
        assert config.get_ui_pref("window_y") == 200

    def test_ui_pref_persists_after_save_and_reload(self, tmp_path):
        path = tmp_path / "config.json"
        config = Config(config_path=path)
        config.set_ui_pref("window_x", 123)
        config.set_ui_pref("always_on_top", False)
        config.save()
        config2 = Config(config_path=path)
        assert config2.get_ui_pref("window_x") == 123
        assert config2.get_ui_pref("always_on_top") is False

    def test_set_ui_pref_creates_section_if_missing(self, tmp_path):
        """set_ui_pref works even if ui_preferences key is absent."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "dev"}))
        config = Config(config_path=path)
        # Remove ui_preferences to simulate a pre-v0.6.0 config
        config._config.pop("ui_preferences", None)
        config.set_ui_pref("window_x", 50)
        assert config.get_ui_pref("window_x") == 50

    def test_get_ui_pref_with_corrupted_section_returns_default(self, tmp_path):
        """Sanitization repairs a non-dict ui_preferences back to defaults."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": "bad_value"}))
        config = Config(config_path=path)
        # After sanitization the section is the default dict; window_x default is None.
        assert config.get_ui_pref("window_x") is None
        assert isinstance(config.get_ui_pref("opacity"), float)


# ------------------------------------------------------------------
# v0.7.0 - Theme settings
# ------------------------------------------------------------------


class TestConfigThemeSettings:
    def test_default_theme_name_is_matrix(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get_theme_setting("name") == "matrix"

    def test_get_theme_setting_missing_key_returns_default(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        assert config.get_theme_setting("nonexistent", "fallback") == "fallback"

    def test_set_theme_name(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        config.set_theme_setting("name", "dark")
        assert config.get_theme_setting("name") == "dark"

    def test_set_theme_custom_colors(self, tmp_path):
        config = Config(config_path=tmp_path / "config.json")
        custom = {"bg": "#102030", "fg": "#c0d0e0", "accent": "#203040"}
        config.set_theme_setting("custom", custom)
        assert config.get_theme_setting("custom") == custom

    def test_theme_settings_persist_after_save_reload(self, tmp_path):
        path = tmp_path / "config.json"
        config = Config(config_path=path)
        config.set_theme_setting("name", "light")
        config.save()
        config2 = Config(config_path=path)
        assert config2.get_theme_setting("name") == "light"

    def test_set_theme_creates_section_if_missing(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "dev"}))
        config = Config(config_path=path)
        config._config.pop("theme", None)
        config.set_theme_setting("name", "dark")
        assert config.get_theme_setting("name") == "dark"

    def test_get_theme_setting_with_corrupted_section_returns_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"theme": "bad_string"}))
        config = Config(config_path=path)
        assert config.get_theme_setting("name", "matrix") == "matrix"

    def test_custom_theme_colors_persist(self, tmp_path):
        path = tmp_path / "config.json"
        config = Config(config_path=path)
        config.set_theme_setting("name", "custom")
        config.set_theme_setting(
            "custom", {"bg": "#aabbcc", "fg": "#112233", "accent": "#445566"}
        )
        config.save()
        config2 = Config(config_path=path)
        assert config2.get_theme_setting("name") == "custom"
        custom = config2.get_theme_setting("custom")
        assert custom["bg"] == "#aabbcc"
        assert custom["fg"] == "#112233"


# ------------------------------------------------------------------
# v0.1.0 - Config migration (deep merge)
# ------------------------------------------------------------------


class TestConfigDeepMerge:
    """Ensure nested config sub-dicts are deep-merged, not replaced wholesale."""

    def test_partial_ui_prefs_keeps_defaults(self, tmp_path):
        """Old config with only window_x should not lose always_on_top default."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": {"window_x": 100}}))
        config = Config(config_path=path)
        assert config.get_ui_pref("window_x") == 100
        assert config.get_ui_pref("always_on_top") is True  # kept from defaults
        assert config.get_ui_pref("opacity") == pytest.approx(0.90)

    def test_partial_timer_settings_keeps_defaults(self, tmp_path):
        """Old config with only one timer_setting should not drop other defaults."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"timer_settings": {"max_backup_files": 10}}))
        config = Config(config_path=path)
        assert config.get_timer_setting("max_backup_files") == 10
        assert config.get_timer_setting("autosave_interval_minutes") == 1
        assert config.get_timer_setting("date_format") == "DD/MM/YYYY"

    def test_partial_theme_keeps_defaults(self, tmp_path):
        """Old config theme dict is merged, not replaced."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"theme": {"name": "dark"}}))
        config = Config(config_path=path)
        assert config.get_theme_setting("name") == "dark"
        # custom sub-dict should still be present from defaults
        assert config.get_theme_setting("custom") is not None

    def test_top_level_scalar_overrides_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "dev"}))
        config = Config(config_path=path)
        assert config.environment.value == "dev"

    def test_deep_merge_does_not_add_unknown_keys_to_defaults(self, tmp_path):
        """Unknown keys from file are still accepted (no strict schema)."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"custom_field": "hello"}))
        config = Config(config_path=path)
        assert config.get("custom_field") == "hello"


# ------------------------------------------------------------------
# v0.1.0 - Config sanitization (invalid values don't crash app)
# ------------------------------------------------------------------


class TestConfigSanitization:
    def test_invalid_opacity_too_high_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": {"opacity": 5.0}}))
        config = Config(config_path=path)
        assert 0.3 <= config.get_ui_pref("opacity") <= 1.0

    def test_invalid_opacity_too_low_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": {"opacity": 0.0}}))
        config = Config(config_path=path)
        assert 0.3 <= config.get_ui_pref("opacity") <= 1.0

    def test_invalid_opacity_string_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": {"opacity": "bright"}}))
        config = Config(config_path=path)
        assert config.get_ui_pref("opacity") == pytest.approx(0.90)

    def test_invalid_always_on_top_string_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": {"always_on_top": "yes"}}))
        config = Config(config_path=path)
        assert isinstance(config.get_ui_pref("always_on_top"), bool)

    def test_invalid_window_x_string_becomes_none(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": {"window_x": "left"}}))
        config = Config(config_path=path)
        assert config.get_ui_pref("window_x") is None

    def test_valid_window_x_int_string_is_coerced(self, tmp_path):
        """window_x stored as a JSON number is accepted; string form is rejected."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": {"window_x": 200}}))
        config = Config(config_path=path)
        assert config.get_ui_pref("window_x") == 200

    def test_invalid_autosave_interval_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({"timer_settings": {"autosave_interval_minutes": 7}})
        )
        config = Config(config_path=path)
        assert config.get_timer_setting("autosave_interval_minutes") == 1

    def test_invalid_autosave_interval_string_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({"timer_settings": {"autosave_interval_minutes": "fast"}})
        )
        config = Config(config_path=path)
        assert config.get_timer_setting("autosave_interval_minutes") == 1

    def test_invalid_time_rounding_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"timer_settings": {"time_rounding_minutes": 3}}))
        config = Config(config_path=path)
        assert config.get_timer_setting("time_rounding_minutes") == 0

    def test_invalid_date_format_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"timer_settings": {"date_format": "YYYY/DD/MM"}}))
        config = Config(config_path=path)
        assert config.get_timer_setting("date_format") == "DD/MM/YYYY"

    def test_invalid_time_format_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"timer_settings": {"time_format": "military"}}))
        config = Config(config_path=path)
        assert config.get_timer_setting("time_format") == "24h"

    def test_invalid_max_backup_files_zero_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"timer_settings": {"max_backup_files": 0}}))
        config = Config(config_path=path)
        assert config.get_timer_setting("max_backup_files") >= 1

    def test_invalid_max_backup_files_negative_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"timer_settings": {"max_backup_files": -5}}))
        config = Config(config_path=path)
        assert config.get_timer_setting("max_backup_files") >= 1

    def test_invalid_activity_history_retention_days_resets_to_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({"timer_settings": {"activity_history_retention_days": 0}})
        )
        config = Config(config_path=path)
        assert config.get_timer_setting("activity_history_retention_days") == 3650

    def test_invalid_ui_prefs_not_dict_resets_to_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"ui_preferences": "corrupt"}))
        config = Config(config_path=path)
        assert isinstance(config.get_ui_pref("opacity"), float)

    def test_invalid_timer_settings_not_dict_resets_to_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"timer_settings": 42}))
        config = Config(config_path=path)
        assert isinstance(config.get_timer_setting("autosave_interval_minutes"), int)

    def test_invalid_theme_not_dict_resets_to_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"theme": "neon"}))
        config = Config(config_path=path)
        assert isinstance(config.get_theme_setting("name"), str)

    def test_invalid_custom_theme_colors_reset_to_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps(
                {
                    "theme": {
                        "name": "custom",
                        "custom": {
                            "bg": "invalid",
                            "fg": "#123",
                            "accent": "#gggggg",
                        },
                    }
                }
            )
        )
        config = Config(config_path=path)
        custom = config.get_theme_setting("custom")
        assert custom["bg"] == "#001100"
        assert custom["fg"] == "#00FF00"
        assert custom["accent"] == "#003300"

    def test_valid_values_are_not_changed(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps(
                {
                    "ui_preferences": {"opacity": 0.7, "always_on_top": False},
                    "timer_settings": {
                        "autosave_interval_minutes": 5,
                        "time_rounding_minutes": 15,
                        "date_format": "MM/DD/YYYY",
                        "time_format": "12h",
                        "max_backup_files": 3,
                    },
                }
            )
        )
        config = Config(config_path=path)
        assert config.get_ui_pref("opacity") == pytest.approx(0.7)
        assert config.get_ui_pref("always_on_top") is False
        assert config.get_timer_setting("autosave_interval_minutes") == 5
        assert config.get_timer_setting("time_rounding_minutes") == 15
        assert config.get_timer_setting("date_format") == "MM/DD/YYYY"
        assert config.get_timer_setting("time_format") == "12h"
        assert config.get_timer_setting("max_backup_files") == 3


# ------------------------------------------------------------------
# v0.1.0 - Config version migration
# ------------------------------------------------------------------


class TestConfigVersionMigration:
    def test_old_config_version_triggers_save(self, tmp_path):
        """Loading a config with old config_version must update and save it."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"config_version": "0.0.1", "environment": "dev"}))
        Config(config_path=path)
        saved = json.loads(path.read_text())
        assert saved["config_version"] == Config.DEFAULT_CONFIG["config_version"]

    def test_current_config_version_is_not_resaved_unnecessarily(self, tmp_path):
        """No spurious resave when config_version already matches."""
        path = tmp_path / "config.json"
        current_version = Config.DEFAULT_CONFIG["config_version"]
        path.write_text(json.dumps({"config_version": current_version}))
        mtime_before = path.stat().st_mtime
        import time as _time

        _time.sleep(0.05)
        Config(config_path=path)
        # mtime should be unchanged (no save triggered)
        assert path.stat().st_mtime == pytest.approx(mtime_before, abs=0.01)

    def test_migrated_config_preserves_user_values(self, tmp_path):
        """After migration, the user's settings are intact in the saved file."""
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps(
                {
                    "config_version": "0.0.1",
                    "environment": "dev",
                    "ui_preferences": {"window_x": 999},
                }
            )
        )
        Config(config_path=path)
        saved = json.loads(path.read_text())
        assert saved["environment"] == "dev"
        assert saved["ui_preferences"]["window_x"] == 999

    def test_migrated_config_gains_new_default_keys(self, tmp_path):
        """After migration, new default keys are present in the saved file."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"config_version": "0.0.1"}))
        Config(config_path=path)
        saved = json.loads(path.read_text())
        assert "timer_settings" in saved
        assert "ui_preferences" in saved

    def test_missing_config_version_triggers_migration(self, tmp_path):
        """A config file without config_version is treated as outdated."""
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"environment": "prod"}))
        Config(config_path=path)
        saved = json.loads(path.read_text())
        assert saved["config_version"] == Config.DEFAULT_CONFIG["config_version"]
