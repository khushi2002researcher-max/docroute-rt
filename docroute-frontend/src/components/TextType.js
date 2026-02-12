import { useEffect, useState } from "react";
import "./TextType.css";

const TextType = ({
  text,
  typingSpeed = 50,
  pauseDuration = 1500,
  loop = true,
  showCursor = true,
  cursorCharacter = "|",
  className = "",
}) => {
  const [displayedText, setDisplayedText] = useState("");
  const [index, setIndex] = useState(0);

  const textArray = Array.isArray(text) ? text : [text];
  const currentText = textArray[index % textArray.length];

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setDisplayedText(currentText.slice(0, i + 1));
      i++;

      if (i === currentText.length) {
        clearInterval(interval);
        if (loop) {
          setTimeout(() => {
            setIndex((prev) => prev + 1);
            setDisplayedText("");
          }, pauseDuration);
        }
      }
    }, typingSpeed);

    return () => clearInterval(interval);
  }, [currentText, typingSpeed, pauseDuration, loop]);

  return (
    <span className={`text-type ${className}`}>
      {displayedText}
      {showCursor && <span className="text-type__cursor">{cursorCharacter}</span>}
    </span>
  );
};

export default TextType;
