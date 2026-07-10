import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

type Lang = 'th' | 'en'

const dict: Record<Lang, Record<string, string>> = {
  th: {
    app_name: 'HomeKeeper',
    tagline: 'ดูแลบ้าน รถ และทรัพย์สินตลอดอายุการใช้งาน',
    login: 'เข้าสู่ระบบ',
    logout: 'ออกจากระบบ',
    register: 'สมัครสมาชิก',
    email: 'อีเมล',
    password: 'รหัสผ่าน',
    full_name: 'ชื่อ-นามสกุล',
    or_continue_with: 'หรือเข้าสู่ระบบด้วย',
    home: 'หน้าหลัก',
    call_technician: 'เรียกช่าง',
    call_urgent: 'เรียกช่างด่วน',
    my_homes: 'บ้านของฉัน',
    my_jobs: 'งานของฉัน',
    account: 'บัญชี',
    security: 'ความปลอดภัย',
    search_service: 'ค้นหาบริการ',
    popular_categories: 'หมวดบริการยอดนิยม',
    in_progress: 'งานที่กำลังดำเนินการ',
    maintenance_due: 'ถึงกำหนดบำรุงรักษา',
    add_property: 'เพิ่มบ้าน/ทรัพย์สิน',
    add_asset: 'เพิ่มอุปกรณ์',
    create_job: 'สร้างคำขอเรียกช่าง',
    submit: 'ยืนยัน',
    cancel: 'ยกเลิก',
    save: 'บันทึก',
    status: 'สถานะ',
    admin: 'ผู้ดูแลระบบ',
    dashboard: 'แดชบอร์ด',
    dispatch: 'มอบหมายงาน',
    technician: 'ช่าง',
    new_jobs: 'งานใหม่',
    onboarding_title: 'ตั้งค่าบัญชีของคุณ',
    accept_terms: 'ยอมรับเงื่อนไขการใช้งานและนโยบายความเป็นส่วนตัว',
    health_record: 'ประวัติการดูแลบ้าน',
    quotation: 'ใบเสนอราคา',
    approve: 'อนุมัติ',
    reject: 'ปฏิเสธ',
    notifications: 'การแจ้งเตือน',
  },
  en: {
    app_name: 'HomeKeeper',
    tagline: 'Care for your home, car and assets for their entire lifetime',
    login: 'Log in',
    logout: 'Log out',
    register: 'Sign up',
    email: 'Email',
    password: 'Password',
    full_name: 'Full name',
    or_continue_with: 'Or continue with',
    home: 'Home',
    call_technician: 'Book a technician',
    call_urgent: 'Emergency call',
    my_homes: 'My homes',
    my_jobs: 'My jobs',
    account: 'Account',
    security: 'Security',
    search_service: 'Search services',
    popular_categories: 'Popular categories',
    in_progress: 'Jobs in progress',
    maintenance_due: 'Maintenance due',
    add_property: 'Add property',
    add_asset: 'Add asset',
    create_job: 'Create service request',
    submit: 'Submit',
    cancel: 'Cancel',
    save: 'Save',
    status: 'Status',
    admin: 'Admin',
    dashboard: 'Dashboard',
    dispatch: 'Dispatch',
    technician: 'Technician',
    new_jobs: 'New jobs',
    onboarding_title: 'Set up your account',
    accept_terms: 'I accept the Terms of Service and Privacy Policy',
    health_record: 'Home Health Record',
    quotation: 'Quotation',
    approve: 'Approve',
    reject: 'Reject',
    notifications: 'Notifications',
  },
}

interface I18n {
  lang: Lang
  setLang: (l: Lang) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18n>({ lang: 'th', setLang: () => {}, t: (k) => k })

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>((localStorage.getItem('hk_lang') as Lang) || 'th')
  const value = useMemo<I18n>(
    () => ({
      lang,
      setLang: (l) => {
        localStorage.setItem('hk_lang', l)
        setLangState(l)
      },
      t: (key) => dict[lang][key] ?? key,
    }),
    [lang],
  )
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export const useI18n = () => useContext(I18nContext)
