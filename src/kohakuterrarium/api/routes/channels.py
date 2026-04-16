"""Channel list + send routes."""

from fastapi import APIRouter, Depends, HTTPException

from kohakuterrarium.api.deps import get_manager
from kohakuterrarium.api.schemas import ChannelSend
from kohakuterrarium.llm.message import FilePart, ImagePart, TextPart, VideoPart

router = APIRouter()


def _build_channel_content(message: str, attachments) -> str | list:
    parts = []
    if message:
        parts.append(TextPart(text=message))
    for item in attachments or []:
        att_type = str(getattr(item, "type", "") or "").lower()
        mime_type = str(getattr(item, "mimeType", "") or "")
        url = str(getattr(item, "url", "") or "")
        name = str(getattr(item, "name", "") or "attachment")
        if not url:
            continue
        if att_type == "image" or mime_type.startswith("image/"):
            parts.append(
                ImagePart(
                    url=url,
                    detail="low",
                    source_type="attachment",
                    source_name=name,
                )
            )
        elif att_type == "video" or mime_type.startswith("video/"):
            parts.append(VideoPart(data=url, mime_type=mime_type or "video/mp4", filename=name))
        elif mime_type == "application/pdf" or att_type == "pdf":
            parts.append(FilePart(data=url, mime_type="application/pdf", filename=name))
        else:
            parts.append(TextPart(text=f"[{att_type or 'file'} attachment: {name}]"))
    if not parts:
        return ""
    if len(parts) == 1 and isinstance(parts[0], TextPart):
        return parts[0].text
    return parts


@router.get("")
async def list_channels(terrarium_id: str, manager=Depends(get_manager)):
    """List all channels in a terrarium."""
    try:
        return manager.terrarium_channel_list(terrarium_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{channel_name}/send")
async def send_message(
    terrarium_id: str,
    channel_name: str,
    req: ChannelSend,
    manager=Depends(get_manager),
):
    """Send a message to a channel."""
    try:
        msg_id = await manager.terrarium_channel_send(
            terrarium_id,
            channel_name,
            _build_channel_content(req.content, req.attachments),
            req.sender,
            reasoning_effort=req.reasoning_effort,
        )
        return {"message_id": msg_id, "status": "sent"}
    except Exception as e:
        raise HTTPException(400, str(e))
