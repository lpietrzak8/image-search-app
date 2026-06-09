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
    savedPhotos: Map<string,any>;
    savingPhoto: string | null;
    handleSavePhoto: (img: object) => void;
    handleDeletePhoto: (img: object) => void;
    results: any[];
    setResults: (results: any[]) => void;
}


const Post = ({
    img,
    onClose,
    isLoggedIn,
    savedPhotos,
    savingPhoto,
    handleSavePhoto,
    handleDeletePhoto,
    results,
    setResults,
              } : PostProps)=> {

    const [isSuspended, setIsSuspended] = useState<boolean>(false);
    const [message, setMessage] = useState<string | null>(null);

    const toggleSave = () => {
        try {
            if (savedPhotos.has(img.source_url)) {
                handleDeletePhoto(img);
            } else {
                handleSavePhoto(img);
            }
        }
        catch (error: any) {
            setMessage(error.message || "Something went wrong");
            setTimeout(() => {
                setMessage(null);
            }, 3000)
        }

    }

    const suspendPost = () => {
        axios
            .post("/api/blacklist/suspend", {
            source_url: img.source_url,
            provider: img.provider,
            reason: null
        })
            .then(response => {
                setIsSuspended(true);
                setMessage(response.data.message);
                setResults(results.filter(photo => photo.id != img.id));

            })
            .catch(err => {
                console.log(err);
                setMessage("Something went wrong");
            })
            .finally(() => {
                setTimeout(() => {
                    setMessage(null);
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
                    {message && (
                        <div className={"suspendMessage"}>{message}</div>
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
                                className={`save-btn ${savedPhotos.has(img.source_url) ? "saved" : ""}`}
                                onClick={() => toggleSave()}
                                disabled={savingPhoto === img.image_url}
                                title={savedPhotos.has(img.source_url) ? "Delete" : "Save to My Resources"}
                            >
                                {savedPhotos.has(img.source_url) ? "✓" : "+"}
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