import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Trash2 } from 'lucide-react';
import { addDefaultQuickReplies, addQuickReply, chatErrorMessage, deleteQuickReply, getQuickReplies } from '../chatApi';
import { showToast } from '../../../stores/useToastStore';
import './QuickReplyPicker.css';

// 8단계: 상담원의 자주 쓰는 문구 — 입력칸 왼쪽 [자주 쓰는 문구 ▾] 를 누르면 펼쳐진다
// 고르면 입력칸에 넣고 닫힌다 (바로 보내지 않고 고쳐 보낼 수 있게). 펼친 목록 안에서 추가 · 삭제
// 문구는 상담원마다 따로 서버에 저장 (등록 · 삭제 후 서버가 바뀐 목록을 돌려준다)
export default function QuickReplyPicker({ onPick, disabled }) {
  const [open, setOpen] = useState(false);
  const [replies, setReplies] = useState([]);
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    getQuickReplies().then(setReplies).catch(() => setReplies([]));
  }, []);

  // 목록 바깥을 누르면 닫는다
  useEffect(() => {
    if (!open) return undefined;
    const closeOutside = (event) => {
      if (!boxRef.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener('mousedown', closeOutside);
    return () => document.removeEventListener('mousedown', closeOutside);
  }, [open]);

  async function save(action, done) {
    setSaving(true);
    try {
      setReplies(await action());
      showToast(done);
      return true;
    } catch (error) {
      showToast(chatErrorMessage(error, '저장하지 못했습니다.'));
      return false;
    } finally {
      setSaving(false);
    }
  }

  function pick(content) {
    onPick(content);
    setOpen(false);
  }

  // 입력칸 form 안에 있어서 Enter 가 메시지 보내기로 가지 않게 직접 막는다
  async function handleAdd(event) {
    event.preventDefault();
    if (text.trim() && await save(() => addQuickReply(text.trim()), '문구를 등록했습니다.')) setText('');
  }

  return (
    <div className="quick-picker" ref={boxRef}>
      <button type="button" className="quick-picker-toggle" aria-expanded={open} disabled={disabled} onClick={() => setOpen((v) => !v)}>
        자주 쓰는 문구 <ChevronDown size={14} aria-hidden="true" />
      </button>
      {open && (
        <div className="quick-picker-menu" role="dialog" aria-label="자주 쓰는 문구">
          {replies.length === 0 ? (
            <div className="quick-picker-empty">
              <p>등록한 문구가 없어요.</p>
              <button type="button" disabled={saving}
                onClick={() => save(addDefaultQuickReplies, '기본 문구를 넣었습니다.')}>기본 문구 넣기</button>
            </div>
          ) : (
            <ul>
              {replies.map((reply) => (
                <li key={reply.id}>
                  <button type="button" className="quick-picker-item" onClick={() => pick(reply.content)}>{reply.content}</button>
                  <button type="button" className="quick-picker-delete" aria-label={`"${reply.content}" 삭제`} disabled={saving}
                    onClick={() => save(() => deleteQuickReply(reply.id), '문구를 지웠습니다.')}>
                    <Trash2 size={14} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className="quick-picker-add">
            <input value={text} onChange={(event) => setText(event.target.value)} maxLength={200} placeholder="새 문구 (20개까지)"
              onKeyDown={(event) => event.key === 'Enter' && handleAdd(event)} aria-label="새 문구" />
            <button type="button" disabled={saving || !text.trim()} onClick={handleAdd}>추가</button>
          </div>
        </div>
      )}
    </div>
  );
}
