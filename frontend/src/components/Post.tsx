import {Link} from "react-router-dom";
import { FiFlag } from "react-icons/fi";
import axios from "axios";
import {useEffect, useState} from "react";
import "./Post.css";

type AuthorProps = {
    name: string;
    url: string;
}

type imageProps = {
    id: string;
    author: AuthorProps;
    description: string;
    keywords: string[];
    image_url: string;
    source_url: string;
    provider: string;
}

type PostProps = {
    img: imageProps;
    onClose: () => void;
    isLoggedIn: boolean;
    savedPhotos: Set<string>;
    savingPhoto: string | null;
    handleSavePhoto: (img: object) => void;
}


const Post = ({
    img,
    onClose,
    isLoggedIn,
    savedPhotos,
    savingPhoto,
    handleSavePhoto,
              } : PostProps)=> {

    const [isSuspended, setIsSuspended] = useState<boolean>(false);
    const [suspendMessage, setSuspendMessage] = useState<string | null>(null);


    const suspendPost = () => {
        axios
            .post("/api/blacklist/suspend", {
            source_url: img.source_url,
            provider: img.provider,
            reason: null
        })
            .then(_ => {
                setIsSuspended(true);
                setSuspendMessage("Post suspended");
            })
            .catch(err => {
                console.log(err);
                setSuspendMessage("Something went wrong");
            })
            .finally(() => {
                setTimeout(() => {
                    setSuspendMessage(null);
                }, 3000)
            })
    }

    useEffect(() => {
        document.body.classList.add("modal-open");
        return () => {
            document.body.classList.remove("modal-open");
        }
    }, [])

    return (
        <div className={"modal-overlay"} onClick={onClose}>
            <div className={"postContainer"} onClick={(e) => e.stopPropagation()}>
                <div className={"photoContainer"}>
                    {suspendMessage && (
                        <div className={"suspendMessage"}>{suspendMessage}</div>
                    )}
                    <img src={img.image_url} alt={img.description || "Could not load the photo"} />
                    <div className={"saveButtonsContainer"}>
                        <a
                            className="download-btn"
                            href={img.image_url}
                            download
                            title="Download image"
                        >
                            ⬇
                        </a>
                        {isLoggedIn && (
                            <button
                                className={`save-btn ${savedPhotos.has(img.image_url) ? "saved" : ""}`}
                                onClick={() => handleSavePhoto(img)}
                                disabled={savingPhoto === img.image_url || savedPhotos.has(img.image_url)}
                                title={savedPhotos.has(img.image_url) ? "Saved" : "Save to My Resources"}
                            >
                                {savedPhotos.has(img.image_url) ? "✓" : "+"}
                            </button>
                        )}
                    </div>
                </div>
                <div className={"propertiesContainer"}>
                    <div className={"buttonsContainer"}>
                        <button className={"suspendButton"} onClick={() => !isSuspended && suspendPost()}>
                            <FiFlag stroke={"white"} fill={isSuspended ? "white" : "none"} />
                        </button>
                        <button className={"modal-close"} onClick={onClose}>✕</button>
                    </div>
                    <ul className={"propertiesList"}>
                        <li className={"propertiesItem"}>
                            Picture by {img.author.name} on{" "}
                            <Link to={img.author.url} >{img.provider}</Link>
                        </li>
                        <li className={"propertiesItem"}>
                            <div className={"propertyName"}>Keywords:</div>
                            <ul className={"keywordsList"}>
                                {img.keywords.map((keyword, index) => <li key={index}>{keyword}</li>)}
                            </ul>
                        </li>
                        <li className={"propertiesItem"}>
                            <div className={"propertyName"}>Source:</div> <Link to={img.source_url}>{img.source_url}</Link>
                        </li>
                        {img.description && (
                            <li className={"propertiesItem"}><div className={"propertyName"}>Description:</div> {img.description}</li>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    )
}

export default Post;