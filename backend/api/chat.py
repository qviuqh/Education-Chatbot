"""
Chat API - Endpoint chat với RAG
"""
import asyncio
import anyio

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator

from .. import schemas, models
from ..db import get_db
from ..deps import get_current_user, get_user_conversation
from ..services import conversation_service, rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat với AI - trả về câu trả lời hoàn chỉnh
    """
    # Verify conversation ownership
    conversation = conversation_service.get_conversation_by_id(
        db,
        chat_request.conversation_id,
        current_user.id
    )
    
    # Lưu user message
    user_message = conversation_service.save_message(
        db,
        chat_request.conversation_id,
        role="user",
        content=chat_request.question
    )
    
    try:
        # Get answer từ RAG
        answer = rag_service.answer_question_for_conversation(
            db,
            chat_request.conversation_id,
            chat_request.question,
            streaming=False
        )
        
        # Lưu assistant message
        assistant_message = conversation_service.save_message(
            db,
            chat_request.conversation_id,
            role="assistant",
            content=answer
        )
        
        return schemas.ChatResponse(
            answer=answer,
            conversation_id=chat_request.conversation_id,
            message_id=assistant_message.id
        )
        
    except Exception as e:
        # Log error và trả về message thân thiện
        error_message = "Xin lỗi, tôi không thể trả lời câu hỏi này. Vui lòng thử lại."
        
        # Lưu error message
        conversation_service.save_message(
            db,
            chat_request.conversation_id,
            role="assistant",
            content=error_message
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stream")
async def chat_stream(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat với AI - streaming response (SSE)
    """
    # Verify conversation ownership
    conversation = conversation_service.get_conversation_by_id(
        db,
        chat_request.conversation_id,
        current_user.id
    )
    
    # Lưu user message
    user_message = conversation_service.save_message(
        db,
        chat_request.conversation_id,
        role="user",
        content=chat_request.question
    )
    
    async def generate_response() -> AsyncGenerator[str, None]:
        """
        Generator để stream response. 
        
        Chuyển phần sinh chuỗi đồng bộ sang thread để tránh block event loop
        (quan trọng khi chạy trong container) và gửi SSE từng chunk.
        """
        try:
            full_answer = ""
            
            # Get streaming answer từ RAG
            answer_generator = rag_service.answer_question_for_conversation(
                db,
                chat_request.conversation_id,
                chat_request.question,
                streaming=True
            )
            
            # Đọc generator đồng bộ trong thread để không chặn event loop
            while True:
                chunk = await anyio.to_thread.run_sync(next, answer_generator, None)
                if chunk is None:
                    break
                
                full_answer += chunk
                # Format SSE
                yield f"data: {chunk}\n\n"
                
                await asyncio.sleep(0)  # Nhả control cho event loop
            
            # Lưu complete answer
            conversation_service.save_message(
                db,
                chat_request.conversation_id,
                role="assistant",
                content=full_answer
            )
            
            # Send done signal
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            yield f"data: {error_message}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
