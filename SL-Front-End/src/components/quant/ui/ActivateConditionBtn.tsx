import { FieldPanel } from './FieldPanel';

interface ActivateConditionBtnProps {
    checked: boolean;
    onChange: (checked: boolean) => void;
}

const ActivateConditionBtn = ({ checked, onChange }: ActivateConditionBtnProps) => {
    return (
        <FieldPanel conditionType="sell" className="flex justify-center items-center">
            <button
                onClick={() => onChange(!checked)}
                className="border border-accent-primary text-accent-primary bg-bg-muted w-[10rem] h-[1.625rem] rounded px-10 py-[0.375rem] text-[0.75rem] font-semibold flex justify-center items-center">
                조건 활성화하기
            </button>
        </FieldPanel>
    )
}

export default ActivateConditionBtn