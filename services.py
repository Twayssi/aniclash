import httpx

def search_anime(query: str, page: int = 1):
    url = 'https://graphql.anilist.co'
    graphql_query = '''    
    query ($search: String, $page: Int) {   
        Page(page: $page, perPage: 10) { 
            media(search: $search, type: ANIME) {   
                id
                title { 
                    romaji
                    english
                }
                coverImage {    
                    large
                }
            }
        }
    }
    '''
    response = httpx.post(url=url, json={'query': graphql_query, 'variables': {'search': query, 'page': page}})
    return response.json()


def get_popular_anime(page: int = 1):
    url = 'https://graphql.anilist.co'
    graphql_query = '''    
    query ($page: Int) {   
        Page(page: $page, perPage: 10) { 
            media(type: ANIME, sort: POPULARITY_DESC) {   
                id
                title { 
                    romaji
                    english
                }
                coverImage {    
                    large
                }
            }
        }
    }
    '''
    response = httpx.post(url=url, json={'query': graphql_query, 'variables': {'page': page}})
    return response.json()


def search_anime_by_id(anime_id: int):
    url = 'https://graphql.anilist.co'
    graphql_query = '''    
    query ($id: Int) {   
        Media(id: $id, type: ANIME) {   
            id
            title { 
                romaji
                english
            }
            coverImage {    
                large
            }
        }
    }
    '''
    response = httpx.post(url=url, json={'query': graphql_query, 'variables': {'id': anime_id}})
    return response.json()