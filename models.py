from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, JSON, Enum, BigInteger, Numeric, UniqueConstraint 
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base, engine
from enums import RuleCategory

# レシピテンプレートとルールテンプレートの多対多関係を管理する中間テーブル
class RecipeTemplateRuleTemplate(Base):
    __tablename__ = "recipe_templates_rule_templates"
    
    recipe_template_id = Column(Integer, ForeignKey('recipe_templates.id'), primary_key=True)
    rule_template_id = Column(Integer, ForeignKey('rule_templates.id'), primary_key=True)

# レシピとルールの多対多関係を管理する中間テーブル
class RecipeRule(Base):
    __tablename__ = "recipes_rules"
    
    recipe_id = Column(Integer, ForeignKey('recipes.id'), primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), primary_key=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    birthdate = Column(Date, nullable=False)
    postal_code = Column(String(10), nullable=False)
    address = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    occupation = Column(String(100), nullable=False)
    company_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # リレーション
    rule_templates = relationship("RuleTemplate", back_populates="author")
    recipe_templates = relationship("RecipeTemplate", back_populates="author")
    rules = relationship("Rule", back_populates="user")
    recipes = relationship("Recipe", back_populates="user")

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question = Column(String(500), nullable=False)
    selected_answers = Column(String(1000), nullable=False)  # セミコロン区切りの文字列
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Trigger(Base):
    __tablename__ = "triggers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    required_params = Column(JSON, nullable=False)

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    required_params = Column(JSON, nullable=False)

class RuleTemplate(Base):
    __tablename__ = "rule_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    category = Column(Enum(RuleCategory), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    trigger_id = Column(Integer, ForeignKey("triggers.id"), nullable=False)
    trigger_params = Column(JSON, nullable=False)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    action_params = Column(JSON, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    copies_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # リレーション
    author = relationship("User", back_populates="rule_templates")
    trigger = relationship("Trigger")
    action = relationship("Action")
    recipe_templates = relationship("RecipeTemplate", secondary="recipe_templates_rule_templates", back_populates="rule_templates")

class RecipeTemplate(Base):
    __tablename__ = "recipe_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=False, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    copies_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # リレーション
    author = relationship("User", back_populates="recipe_templates")
    rule_templates = relationship("RuleTemplate", secondary="recipe_templates_rule_templates", back_populates="recipe_templates")

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    category = Column(Enum(RuleCategory), nullable=False)
    template_id = Column(Integer, ForeignKey("rule_templates.id"), nullable=True)
    trigger_id = Column(Integer, ForeignKey("triggers.id"), nullable=False)
    trigger_params = Column(JSON, nullable=False)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    action_params = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # リレーション
    user = relationship("User", back_populates="rules")
    template = relationship("RuleTemplate")
    trigger = relationship("Trigger")
    action = relationship("Action")
    recipes = relationship("Recipe", secondary="recipes_rules", back_populates="rules")

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    template_id = Column(Integer, ForeignKey("recipe_templates.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # リレーション
    user = relationship("User", back_populates="recipes")
    template = relationship("RecipeTemplate")
    rules = relationship("Rule", secondary="recipes_rules", back_populates="recipes")


# ==== ここから たなぼた 取引・ログ テーブル（B版：FKのみ追加、整数・成功時のみ） ====

class TanabotaTransaction(Base):
    __tablename__ = "tanabota_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False, index=True)
    amount_paid = Column(Numeric(12, 0), nullable=False)         # 円のみ（小数なし）
    tanabota_total = Column(Numeric(12, 0), nullable=False, default=0)  # 円のみ（小数なし）
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 1取引 : 多ログ（DBのON DELETE CASCADEを使うためpassive_deletes=True）
    action_logs = relationship(
        "TanabotaActionLog",
        back_populates="transaction",
        passive_deletes=True
    )

class TanabotaActionLog(Base):
    __tablename__ = "tanabota_action_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id = Column(BigInteger, ForeignKey("tanabota_transactions.id", onupdate="RESTRICT", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False, index=True)
    action_id = Column(Integer, ForeignKey("actions.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False, index=True)

    action_type = Column(String(64), nullable=False)         # 例: 'save_percentage' / 'roundup' / 'fixed'
    action_params_json = Column(JSON, nullable=False)        # 実行時スナップショット
    tanabota_amount = Column(Numeric(12, 0), nullable=False) # 円のみ（小数なし）
    result_json = Column(JSON, nullable=True)                # 外部連携レス等（任意）
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 逆リレーション
    transaction = relationship("TanabotaTransaction", back_populates="action_logs")
    rule = relationship("Rule")     # 参照のみ
    action = relationship("Action") # 参照のみ

# ==== ここまで たなぼた 取引・ログ テーブル ====


Base.metadata.create_all(bind=engine)