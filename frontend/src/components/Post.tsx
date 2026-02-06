import {Link} from "react-router-dom";
import { FiFlag } from "react-icons/fi";
import axios from "axios";
import { useState } from "react";
import "./Post.css";

type AuthorProps = {
    name: string;
    url: string;
}

type PostProps = {
    id: string;
    author: AuthorProps;
    description: string;
    keywords: string[];
    imageUrl: string;
    sourceUrl: string;
    provider: string;
    onClose: () => void;
}


const Post = ({
    author,
    description,
    keywords,
    imageUrl,
    sourceUrl,
    provider,
    onClose,
              } : PostProps)=> {

    const [isSuspended, setIsSuspended] = useState<boolean>(false);
    const [suspendMessage, setSuspendMessage] = useState<string | null>(null);


    const suspendPost = () => {
        axios
            .post("/api/blacklist/suspend", {
            source_url: sourceUrl,
            provider: provider,
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
                }, 4000)
            })
    }

    return (
        <div className={"modal-overlay"} onClick={onClose}>
            <div className={"postContainer"} onClick={(e) => e.stopPropagation()}>
                {suspendMessage && (
                    <div className={"suspendMessage"}>{suspendMessage}</div>
                )}
                <div className={"photoContainer"}>
                    <img src={imageUrl} alt={description || "Could not load the photo"} />
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
                            Picture by {author.name} on <Link to={author.url}>{provider}</Link>
                        </li>
                        <li className={"propertiesItem"}>
                            <div className={"itemName"}>Keywords:</div>
                            <ul className={"keywordsList"}>
                                {keywords.map((keyword, index) => <li key={index}>{keyword}</li>)}
                            </ul>
                        </li>
                        <li className={"propertiesItem"}>
                            <div className={"itemName"}>Source:</div> <Link to={sourceUrl}>{sourceUrl}</Link>
                        </li>
                        <li className={"propertiesItem"}><div className={"itemName"}>Description:</div> {description}</li>
                    </ul>
                </div>
            </div>
        </div>
    )
}

export default Post;