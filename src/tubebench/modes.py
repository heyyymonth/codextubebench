from __future__ import annotations

MODE_CHANNELS: dict[str, frozenset[str]] = {
    "gui_native": frozenset({
        "screenshot",
        "screen_recording",
        "audio_playback",
        "pointer_keyboard",
    }),
    "ui_assisted": frozenset({
        "screenshot",
        "screen_recording",
        "audio_playback",
        "pointer_keyboard",
        "ui_transcript",
        "ui_captions",
        "ui_chapters",
        "ui_description",
        "ui_comments",
        "platform_search",
    }),
    "instrumented_browser": frozenset({
        "screenshot",
        "screen_recording",
        "audio_playback",
        "pointer_keyboard",
        "ui_transcript",
        "ui_captions",
        "ui_chapters",
        "ui_description",
        "ui_comments",
        "platform_search",
        "dom",
        "accessibility_tree",
        "media_element",
        "javascript",
    }),
    "hybrid_enterprise": frozenset({
        "screenshot",
        "screen_recording",
        "audio_playback",
        "pointer_keyboard",
        "ui_transcript",
        "ui_captions",
        "ui_chapters",
        "ui_description",
        "ui_comments",
        "platform_search",
        "dom",
        "accessibility_tree",
        "media_element",
        "javascript",
        "local_file",
        "document",
        "spreadsheet",
    }),
}


def validate_mode_channels(mode: str, channels: list[str]) -> list[str]:
    if mode not in MODE_CHANNELS:
        return [f"unknown mode: {mode}"]
    unsupported = sorted(set(channels) - MODE_CHANNELS[mode])
    return [f"{mode} does not permit channel: {channel}" for channel in unsupported]
