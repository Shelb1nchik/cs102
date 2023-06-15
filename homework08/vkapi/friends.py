import dataclasses
import time
import typing as tp

from vkapi import config  # type: ignore
from vkapi.session import Session

QueryParams = tp.Optional[tp.Dict[str, tp.Union[str, int]]]


@dataclasses.dataclass(frozen=True)
class FriendsResponse:
    count: int
    items: tp.Union[tp.List[int], tp.List[tp.Dict[str, tp.Any]]]


def get_friends(
    user_id: int, count: int = 5000, offset: int = 0, fields: tp.Optional[tp.List[str]] = None
) -> FriendsResponse:
    """
    Получить список идентификаторов друзей пользователя или расширенную информацию
    о друзьях пользователя (при использовании параметра fields).

    :param user_id: Идентификатор пользователя, список друзей для которого нужно получить.
    :param count: Количество друзей, которое нужно вернуть.
    :param offset: Смещение, необходимое для выборки определенного подмножества друзей.
    :param fields: Список полей, которые нужно получить для каждого пользователя.
    :return: Список идентификаторов друзей пользователя или список пользователей.
    """
    domain = config.VK_CONFIG["domain"]
    access_token = config.VK_CONFIG["access_token"]
    version_ = config.VK_CONFIG["version"]
    fields = fields and ", ".join(fields) or ""  # type: ignore
    base = f"{domain}"
    url = f"friends.get?access_token={access_token}&user_id={user_id}&fields={fields}&offset={offset}&count={count}&v={version_}"
    session_ = Session(base)
    get_url = session_.get(url)
    try:
        response = FriendsResponse(get_url.json()["response"]["count"], get_url.json()["response"]["items"])
    except KeyError:
        response = get_url.json()
        print(response)
    return response


class MutualFriends(tp.TypedDict):
    id: int
    common_friends: tp.List[int]
    common_count: int


def get_mutual(
    source_uid: tp.Optional[int] = None,
    target_uid: tp.Optional[int] = None,
    target_uids: tp.Optional[tp.List[int]] = None,
    order: str = "",
    count: tp.Optional[int] = None,
    offset: int = 0,
    progress=None,
) -> tp.Union[tp.List[int], tp.List[MutualFriends]]:
    """
    Получить список идентификаторов общих друзей между парой пользователей.

    :param source_uid: Идентификатор пользователя, чьи друзья пересекаются с друзьями пользователя с идентификатором target_uid.
    :param target_uid: Идентификатор пользователя, с которым необходимо искать общих друзей.
    :param target_uids: Cписок идентификаторов пользователей, с которыми необходимо искать общих друзей.
    :param order: Порядок, в котором нужно вернуть список общих друзей.
    :param count: Количество общих друзей, которое нужно вернуть.
    :param offset: Смещение, необходимое для выборки определенного подмножества общих друзей.
    :param progress: Callback для отображения прогресса.
    """
    domain = config.VK_CONFIG["domain"]
    access_token = config.VK_CONFIG["access_token"]
    version_ = config.VK_CONFIG["version"]
    session_ = Session(domain)
    results_of_requests = []
    if target_uids:
        for i in range(((len(target_uids) - 1) // 100) + 1):
            try:
                url = f"friends.getMutual?access_token={access_token}&source_uid={source_uid}&target_uids={','.join(list(map(str, target_uids)))}&count={count}&offset={i * 100}&v={version_}"
                friends = session_.get(url)
                for friend in friends.json()["response"]:
                    results_of_requests.append(
                        MutualFriends(
                            id=friend["id"],
                            common_friends=list(map(int, friend["common_friends"])),
                            common_count=friend["common_count"],
                        )
                    )
            except KeyError:
                pass
            time.sleep(0.34)
        return results_of_requests
    try:
        url = f"friends.getMutual?access_token={access_token}&source_uid={source_uid}&target_uid={target_uid}&count={count}&offset={offset}&v={version_}"
        friends = session_.get(url)
        results_of_requests.extend(friends.json()["response"])
    except:
        pass
    return results_of_requests


if __name__ == "__main__":
    user_id = 128986446
    resp = get_friends(user_id=user_id, fields=["nickname"])
    users = [user["id"] for user in resp.items if not user.get("deactivated")]  # type: ignore
    friends_number = len(users)
    print("Количество друзей пользователя:", friends_number)
    mutual_friends = get_mutual(source_uid=user_id, target_uid=197696266, count=friends_number)
    mutual_friends_number = len(mutual_friends)
    print("Количество общих друзей пользователя:", mutual_friends_number)
    print("Список id общих друзей пользователя:", mutual_friends)
