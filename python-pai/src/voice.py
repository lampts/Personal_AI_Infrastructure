#!/usr/bin/env python3
"""PAI Voice - Minimal ElevenLabs TTS integration

Reads completion message and speaks it aloud using ElevenLabs API.

Usage:
    pai-voice "Research completed on quantum computing"
    pai-voice "Task finished" --voice researcher
    echo "Completed task" | pai-voice --stdin
"""

import sys
import click
import os
from typing import Optional

try:
    from elevenlabs import generate, play, set_api_key
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# ============================================================
# CONFIGURATION
# ============================================================

# Voice mappings (ElevenLabs voice IDs)
VOICES = {
    "kai": "s3TPKV1kjDlVtZbl4Ksh",
    "researcher": "AXdMgz6evoL7OPd7eU12",
    "engineer": "fATgBRI8wg5KkDFg8vBd",
    "architect": "muZKMsIDGYtIkjjiUS82",
    "designer": "ZF6FPAbjXT4488VcRRnw"
}


# ============================================================
# VOICE GENERATION
# ============================================================

def speak(message: str, voice: str = "kai") -> bool:
    """Generate and play TTS audio for message

    Args:
        message: Text to speak
        voice: Voice name (kai, researcher, engineer, etc.)

    Returns:
        bool: True if successful, False otherwise
    """
    if not ELEVENLABS_AVAILABLE:
        print("⚠️ ElevenLabs not installed (pip install elevenlabs)", file=sys.stderr)
        return False

    # Get API key from environment
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        print("⚠️ ELEVENLABS_API_KEY not set", file=sys.stderr)
        return False

    # Set API key
    set_api_key(api_key)

    # Get voice ID
    voice_id = VOICES.get(voice, VOICES["kai"])

    try:
        # Generate audio
        audio = generate(
            text=message,
            voice=voice_id,
            model="eleven_monolingual_v1"
        )

        # Play audio
        play(audio)

        return True

    except Exception as e:
        print(f"❌ Voice error: {e}", file=sys.stderr)
        return False


# ============================================================
# CLI
# ============================================================

@click.command()
@click.argument("message", required=False)
@click.option("--voice", "-v", default="kai", help="Voice to use")
@click.option("--stdin", is_flag=True, help="Read message from stdin")
@click.option("--silent", "-s", is_flag=True, help="Silent mode (no audio)")
def cli(message: Optional[str], voice: str, stdin: bool, silent: bool):
    """Speak message via ElevenLabs TTS

    Examples:
        pai-voice "Research completed"
        pai-voice "Task done" --voice researcher
        echo "Finished work" | pai-voice --stdin
    """
    # Read from stdin if requested
    if stdin:
        message = sys.stdin.read().strip()

    if not message:
        click.echo("❌ No message provided", err=True)
        click.echo("Usage: pai-voice MESSAGE or pai-voice --stdin", err=True)
        sys.exit(1)

    # Silent mode (just log, don't speak)
    if silent:
        click.echo(f"🔇 Silent: {message}", err=True)
        return

    # Check if ElevenLabs is available
    if not ELEVENLABS_AVAILABLE:
        click.echo("⚠️ ElevenLabs not installed", err=True)
        click.echo("Install: pip install elevenlabs", err=True)
        click.echo(f"📝 Message: {message}", err=True)
        return

    # Speak message
    click.echo(f"🔊 Speaking: {message}", err=True)

    success = speak(message, voice)

    if success:
        click.echo(f"✅ Spoke with {voice} voice", err=True)
    else:
        click.echo("❌ Failed to speak", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
