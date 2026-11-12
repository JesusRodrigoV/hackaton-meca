from app.models.auth import TwoFactorBackupCode

# Alias de compatibilidad con el nombre heredado.
TwoFactorCodes = TwoFactorBackupCode

__all__ = ["TwoFactorBackupCode", "TwoFactorCodes"]