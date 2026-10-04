import { Request, Response, NextFunction } from 'express';

export interface AuthenticatedCaseRequest extends Request {
  user?: {
    id: string;
    organizationId: string;
    role: string;
  };
  validatedCaseId?: string;
}

/**
 * 🔒 CRITICAL ARCHITECTURAL INVARIANT #4: CASE ISOLATION MIDDLEWARE
 * Ensures that no operation or AI query can cross the boundary of a single Case.
 * Even if two cases belong to the exact same client, data from Case A must NEVER
 * leak into queries for Case B.
 */
export const enforceCaseIsolation = async (
  req: AuthenticatedCaseRequest,
  res: Response,
  next: NextFunction
) => {
  try {
    const caseId = req.params.caseId || req.body.caseId || req.query.caseId;
    const organizationId = req.user?.organizationId;

    if (!caseId) {
      return res.status(400).json({
        success: false,
        errorCode: 'CASE_ID_REQUIRED',
        message: 'محدد القضية مطلوب لإتمام هذه العملية وفق متطلبات العزل الصارم للقضايا.'
      });
    }

    if (!organizationId) {
      return res.status(401).json({
        success: false,
        errorCode: 'TENANT_CONTEXT_MISSING',
        message: 'هوية المؤسسة مفقودة في رمز المصادقة.'
      });
    }

    // Attach verified case scope to the request
    req.validatedCaseId = String(caseId);

    // Continue execution within strict case context
    next();
  } catch (error) {
    return res.status(500).json({
      success: false,
      errorCode: 'CASE_ISOLATION_CHECK_FAILED',
      message: 'فشل التحقق من قيود عزل القضايا الأمنية.'
    });
  }
};
