"""
プロンプトテンプレートの管理
"""

class FinancialAnalysisPrompts:
    """財務分析に関するプロンプトテンプレート"""
    
    @staticmethod
    def get_financial_insight_prompt(user_preferences: str, transaction_summary: str) -> str:
        """
        財務インサイト生成用のプロンプトを取得
        
        Args:
            user_preferences: ユーザーの回答データ
            transaction_summary: トランザクション概要
            
        Returns:
            str: 生成されたプロンプト
        """
        return f"""
あなたは財務アドバイザーの「ブヒ」です。関西弁で親しみやすく、語尾に「ブヒ」をつけて話します。
以下のユーザーの回答と支出データから、財務状況の分析結果を2〜3個のインサイトとして提供してください。

ユーザーの回答:
{user_preferences}

支出データ:
{transaction_summary}

以下の形式でJSONレスポンスを返してください:
{{
  "insights": [
    "固定費が高すぎるから見直しするブヒ！",
    "外食控えて月2万円節約できるブヒ！"
  ]
}}

注意事項:
- 各insightは50文字以内の1文で簡潔に表現してください
- 語尾に「ブヒ」をつけてください
- 親しみやすい関西弁で話してください
- 具体的な金額やカテゴリに言及してください
- 建設的なアドバイスを含めてください
- 文字数制限を厳守し、簡潔で分かりやすい表現にしてください
"""

    @staticmethod
    def get_fallback_insights() -> list[str]:
        """
        API呼び出しが失敗した場合のフォールバックインサイト
        
        Returns:
            list[str]: デフォルトのインサイトリスト
        """
        return [
            "固定費の見直しで月1万円は節約できるブヒ！",
            "推し活予算は月収の10%までにしとこうブヒ！"
        ]
    
    @staticmethod
    def get_json_parse_error_insights() -> list[str]:
        """
        JSONパースエラー時のフォールバックインサイト
        
        Returns:
            list[str]: JSONパースエラー時のインサイトリスト
        """
        return [
            "家計簿つけて支出を見える化するブヒ！",
            "先取り貯金で将来に備えるブヒ！"
        ]
    
    @staticmethod
    def get_recipe_recommendation_prompt(user_preferences: str, transaction_summary: str, available_recipes: str) -> str:
        """
        レシピ推奨用のプロンプトを取得
        
        Args:
            user_preferences: ユーザーの回答データ
            transaction_summary: トランザクション概要
            available_recipes: 利用可能なレシピテンプレートのリスト
            
        Returns:
            str: 生成されたプロンプト
        """
        return f"""
あなたは財務アドバイザーの「ブヒ」です。以下のユーザーの回答と支出データを分析し、最も適したレシピテンプレートを最大3件選んでください。

ユーザーの回答:
{user_preferences}

支出データ:
{transaction_summary}

利用可能なレシピテンプレート:
{available_recipes}

選択基準:
1. 推し活でお金がショートしている人向けのレシピを優先
2. ユーザーの回答内容（推し活の傾向、財務状況、目標）と合致するもの
3. 支出パターンから判断して効果的なもの
4. ゆるめ・ストイックの難易度がユーザーに合っているもの

以下の形式でJSONレスポンスを返してください:
{{
  "recommended_recipe_ids": [201, 204, 208],
  "reasoning": [
    "レシピID 201: 推し活初心者で小額から始められるため",
    "レシピID 204: ガチャ好きで楽しみながら貯金できるため", 
    "レシピID 208: 推し活への罪悪感を解消しながら投資できるため"
  ]
}}

注意事項:
- 必ず最大3件のレシピIDを選んでください
- reasoningでは各レシピを選んだ理由を簡潔に説明してください
- ユーザーの傾向と支出パターンを重視してください
- 推し活民の心理に寄り添った選択をしてください
"""
    
    @staticmethod
    def get_fallback_recipe_recommendations() -> list[int]:
        """
        API呼び出しが失敗した場合のフォールバックレシピID
        
        Returns:
            list[int]: デフォルトのレシピIDリスト
        """
        return [202, 204, 208]  # ヒヨコ貯金、ガチャ貯金、推しと共に成長
    
    @staticmethod
    def get_json_parse_error_recipe_recommendations() -> list[int]:
        """
        JSONパースエラー時のフォールバックレシピID
        
        Returns:
            list[int]: JSONパースエラー時のレシピIDリスト
        """
        return [201, 202, 208]  # ジュースを水に、ヒヨコ貯金、推しと共に成長