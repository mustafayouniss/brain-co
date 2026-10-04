/**
 * Egyptian National ID Validator (الرقم القومي المصري - 14 رقم)
 * Validates check logic and extracts century, birthdate, and governorate.
 */

export interface EgyptianNationalIdInfo {
  isValid: boolean;
  birthDate?: Date;
  century?: number;
  governorateCode?: string;
  governorateName?: string;
  gender?: 'male' | 'female';
  error?: string;
}

const GOVERNORATES: Record<string, string> = {
  '01': 'القاهرة',
  '02': 'الإسكندرية',
  '03': 'بورسعيد',
  '04': 'السويس',
  '11': 'دمياط',
  '12': 'الدقهلية',
  '13': 'الشرقية',
  '14': 'القليوبية',
  '15': 'كفر الشيخ',
  '16': 'الغربية',
  '17': 'المنوفية',
  '18': 'البحيرة',
  '19': 'الإسماعيلية',
  '21': 'الجيزة',
  '22': 'بني سويف',
  '23': 'الفيوم',
  '24': 'المنيا',
  '25': 'أسيوط',
  '26': 'سوهاج',
  '27': 'قنا',
  '28': 'أسوان',
  '29': 'الأقصر',
  '31': 'البحر الأحمر',
  '32': 'الوادي الجديد',
  '33': 'مطروح',
  '34': 'شمال سيناء',
  '35': 'جنوب سيناء',
  '88': 'خارج الجمهورية'
};

export function validateEgyptianNationalId(id: string): EgyptianNationalIdInfo {
  const cleaned = id.trim();

  if (!/^[2-3]\d{13}$/.test(cleaned)) {
    return {
      isValid: false,
      error: 'الرقم القومي يجب أن يتكون من 14 رقماً ويبدأ بـ 2 أو 3.'
    };
  }

  const centuryDigit = parseInt(cleaned[0], 10);
  const century = centuryDigit === 2 ? 1900 : 2000;
  const year = century + parseInt(cleaned.substring(1, 3), 10);
  const month = parseInt(cleaned.substring(3, 5), 10);
  const day = parseInt(cleaned.substring(5, 7), 10);

  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return { isValid: false, error: 'تاريخ الميلاد المستخرج من الرقم القومي غير صحيح.' };
  }

  const birthDate = new Date(year, month - 1, day);
  const govCode = cleaned.substring(7, 9);
  const govName = GOVERNORATES[govCode] || 'غير محدد';
  const sequence = parseInt(cleaned.substring(9, 13), 10);
  const gender = sequence % 2 !== 0 ? 'male' : 'female';

  return {
    isValid: true,
    century,
    birthDate,
    governorateCode: govCode,
    governorateName: govName,
    gender
  };
}
