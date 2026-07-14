CREATE TABLE IF NOT EXISTS public.chatbot_token_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    request_id TEXT,
    request_type TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0 CHECK (prompt_tokens >= 0),
    completion_tokens INTEGER NOT NULL DEFAULT 0 CHECK (completion_tokens >= 0),
    total_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT chatbot_token_usage_logs_request_type_not_blank CHECK (length(trim(request_type)) > 0),
    CONSTRAINT chatbot_token_usage_logs_model_not_blank CHECK (length(trim(model)) > 0)
);

CREATE INDEX IF NOT EXISTS chatbot_token_usage_logs_user_created_idx
    ON public.chatbot_token_usage_logs (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS chatbot_token_usage_logs_created_idx
    ON public.chatbot_token_usage_logs (created_at DESC);

ALTER TABLE public.chatbot_token_usage_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "사용자는 자신의 챗봇 실제 토큰 로그만 조회 가능"
    ON public.chatbot_token_usage_logs;
CREATE POLICY "사용자는 자신의 챗봇 실제 토큰 로그만 조회 가능"
    ON public.chatbot_token_usage_logs
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "사용자는 자신의 챗봇 실제 토큰 로그만 생성 가능"
    ON public.chatbot_token_usage_logs;
CREATE POLICY "사용자는 자신의 챗봇 실제 토큰 로그만 생성 가능"
    ON public.chatbot_token_usage_logs
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = user_id);

GRANT SELECT, INSERT ON TABLE public.chatbot_token_usage_logs TO authenticated;
