import { motion } from "motion/react"
import { cn } from "@/lib/utils"
import {useState} from "react";
import type { ComponentPropsWithoutRef } from "react";

const initialProps = {
    pathLength: 0,
    opacity: 0,
} as const

const animateProps = {
    pathLength: 1,
    opacity: 1,
} as const

type Props = ComponentPropsWithoutRef<typeof motion.svg> & {
    speed?: number
    onAnimationComplete?: () => void
}

export function AppleHelloEnglishEffect({ className, speed = 0.8, onAnimationComplete, ...props }: Props) {
    const calc = (x: number) => x * speed

    return (
        <motion.svg
            className={cn("h-20", className)}
            exit={{ opacity: 0 }}
            fill="none"
            initial={{ opacity: 1 }}
            stroke="currentColor"
            strokeWidth="14.8883"
            transition={{ duration: 0.5 }}
            viewBox="0 0 638 200"
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <title>hello</title>

            {/* h1 */}
            <motion.path
                animate={animateProps}
                d="M8.69214 166.553C36.2393 151.239 61.3409 131.548 89.8191 98.0295C109.203 75.1488 119.625 49.0228 120.122 31.0026C120.37 17.6036 113.836 7.43883 101.759 7.43883C88.3598 7.43883 79.9231 17.6036 74.7122 40.9363C69.005 66.5793 64.7866 96.0036 54.1166 190.356"
                initial={initialProps}
                style={{ strokeLinecap: "round" }}
                transition={{
                    duration: calc(0.8),
                    ease: "easeInOut",
                    opacity: { duration: 0.4 },
                }}
            />

            {/* h2, ello */}
            <motion.path
                animate={animateProps}
                d="M55.1624 181.135C60.6251 133.114 81.4118 98.0479 107.963 98.0479C123.844 98.0479 133.937 110.703 131.071 128.817C129.457 139.487 127.587 150.405 125.408 163.06C122.869 178.941 130.128 191.348 152.122 191.348C184.197 191.348 219.189 173.523 237.097 145.915C243.198 136.509 245.68 128.073 245.928 119.884C246.176 104.996 237.739 93.8296 222.851 93.8296C203.992 93.8296 189.6 115.17 189.6 142.465C189.6 171.745 205.481 192.341 239.208 192.341C285.066 192.341 335.86 137.292 359.199 75.8585C365.788 58.513 368.26 42.4065 368.26 31.1512C368.26 17.8057 364.042 7.55823 352.131 7.55823C340.469 7.55823 332.777 16.6141 325.829 30.9129C317.688 47.4967 311.667 71.4162 309.203 98.4549C303 166.301 316.896 191.348 349.936 191.348C390 191.348 434.542 135.534 457.286 75.6686C463.803 58.513 466.275 42.4065 466.275 31.1512C466.275 17.8057 462.057 7.55823 450.146 7.55823C438.484 7.55823 430.792 16.6141 423.844 30.9129C415.703 47.4967 409.682 71.4162 407.218 98.4549C401.015 166.301 414.911 191.348 444.416 191.348C473.874 191.348 489.877 165.67 499.471 138.402C508.955 111.447 520.618 94.8221 544.935 94.8221C565.035 94.8221 580.916 109.71 580.916 137.75C580.916 168.768 560.792 192.093 535.362 192.341C512.984 192.589 498.285 174.475 499.774 147.179C501.511 116.907 519.873 94.8221 543.943 94.8221C557.839 94.8221 569.51 100.999 578.682 107.725C603.549 125.866 622.709 114.656 630.047 96.7186"
                initial={initialProps}
                onAnimationComplete={onAnimationComplete}
                style={{ strokeLinecap: "round" }}
                transition={{
                    duration: calc(2.8),
                    ease: "easeInOut",
                    delay: calc(0.7),
                    opacity: { duration: 0.7, delay: calc(0.7) },
                }}
            />
        </motion.svg>
    )
}

export function ApplePolRAGionEffect({className, speed = 2.0, onAnimationComplete, ...props}: Props) {
    const calc = (x: number) => x * speed

    return (
        <motion.svg
            className={cn("h-20", className)}
            exit={{ opacity: 0 }}
            fill="none"
            initial={{ opacity: 1 }}
            stroke="currentColor"
            strokeWidth="14"
            transition={{ duration: 1.0 }}
            viewBox="0 0 820 200"
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <title>PolRAGion</title>

            {/* P */}
            <motion.path
                animate={animateProps}
                initial={initialProps}
                onAnimationComplete={onAnimationComplete}
                d="
                    M25 175
                    C30 130 35 80 40 25
                    C75 10 115 20 115 55
                    C115 90 80 105 40 95

                    M125 130
                    C125 105 140 90 160 90
                    C185 90 195 110 190 135
                    C185 160 170 175 150 175
                    C130 175 122 155 125 130

                    M215 25
                    C210 75 208 125 210 155
                    C211 170 220 178 235 175

                    M270 175
                    C275 125 278 75 280 25
                    C320 10 355 20 355 55
                    C355 85 325 100 280 95
                    C310 100 340 135 365 175

                    M380 175
                    C395 125 412 75 432 25
                    C450 78 468 128 485 175
                    M397 125
                    C420 120 446 120 468 125

                    M555 55
                    C542 32 520 22 500 32
                    C475 45 472 100 480 135
                    C487 168 512 180 540 168
                    C555 160 562 143 560 122
                    C547 120 533 120 520 122

                    M590 95
                    C588 120 587 150 590 175
                    M592 68
                    C592 67 592 67 592 66

                    M615 130
                    C615 105 630 90 650 90
                    C675 90 685 110 680 135
                    C675 160 660 175 640 175
                    C620 175 612 155 615 130

                    M705 175
                    C708 145 710 115 710 95
                    C725 82 750 88 755 105
                    C760 125 752 150 755 175
                    C757 183 765 185 775 178
                "
                style={{
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                }}
                transition={{
                    duration: calc(1.2),
                    ease: "easeInOut",
                    delay: calc(0.0),
                    opacity: {
                        duration: calc(0.4),
                        delay: calc(0.0)
                    },
                }}
            />
        </motion.svg>
    )
}

export function HelloString({
    textCol,
    fullScreen = false,
    className,
}: {
    textCol: "black" | "white"
    fullScreen?: boolean
    className?: string
}) {
    const [calligraphyWriting, setCalligraphyWriting] = useState<"hello" | "polragion" | "standard">("hello")

    const colText = `text-${textCol}`
    const colBackground = `bg-${textCol === "white" ? "black" : "white"}`

    return (
        <div
            className={cn(
                fullScreen
                    //? "fixed inset-0 flex flex-col items-center justify-center gap-8"
                    ? "fixed inset-0 flex flex-col items-center justify-center gap-8 "
                    : "inline-flex flex-col items-center justify-center gap-8",
                colBackground,
                className
            )}
        >
            {calligraphyWriting === "hello" ? (
                <AppleHelloEnglishEffect
                    className={`${colText} h-24 sm:h-12`}
                    onAnimationComplete={() => setTimeout(() => setCalligraphyWriting("polragion"), 1000)}
                />
            ) : (

                calligraphyWriting === "polragion" ? (
                        <ApplePolRAGionEffect
                            className={`${colText} h-24 sm:h-12`}
                            onAnimationComplete={() => setTimeout(() => setCalligraphyWriting("standard"), 1000)}
                        />
                    ) : (
                        // TODO: Replace with real page
                        <div>OKKKKK</div>
                    )
            )}
        </div>
    )
}
