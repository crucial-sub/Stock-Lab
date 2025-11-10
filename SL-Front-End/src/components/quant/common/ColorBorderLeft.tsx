
type Props = {
    conditionType: 'buy' | 'sell' | 'target'
}

const ColorBorderLeft = ({ conditionType }: Props) => {
    return (
        <div className={`w-1 h-full left-0 top-0 absolute ${conditionType === "buy" ? "bg-brand-primary" : (conditionType === "sell" ? "bg-accent-primary" : "")} rounded-tl-md rounded-bl-md shadow-[0px_0px_8px_0px_rgba(0,0,0,0.10)]`} />
    )
}

export default ColorBorderLeft