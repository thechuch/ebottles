from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.models.schemas import TranscribeResponse
from app.services.openai_service import OpenAIService, get_openai_service
from app.security import require_api_key

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    _: None = Depends(require_api_key),
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    openai_service: OpenAIService = Depends(get_openai_service),
):
    """
    Transcribe audio using OpenAI Whisper.
    
    Accepts audio files (webm, mp3, wav, m4a, etc.) and returns the transcribed text.
    """
    # Validate file type
    allowed_types = [
        "audio/webm",
        "audio/mp3",
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/m4a",
        "audio/mp4",
        "audio/ogg",
        "video/webm",  # MediaRecorder sometimes uses this
    ]
    
    content_type = audio.content_type or ""
    if content_type not in allowed_types:
        # Be lenient - if content type is missing, try anyway
        if content_type and not content_type.startswith(("audio/", "video/")):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {content_type}. Please upload an audio file.",
            )
    
    try:
        # Read the audio file
        audio_bytes = await audio.read()
        
        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty audio file received.",
            )
        # 10MB cap to prevent abuse
        if len(audio_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Audio file too large (max 10MB).")
        
        # Transcribe using Whisper
        text = await openai_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.webm",
        )
        
        return TranscribeResponse(
            status="ok",
            text=text,
            message="",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to transcribe audio. Please try again.",
        )

