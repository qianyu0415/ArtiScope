import { Menus } from '@/types/menu';

export const menuData: Menus[] = [
    {
        id: '1',
        title: 'ArtiScope Generator',
        index: '1',
        icon: 'HomeFilled',
        children: [
            {
                id: '11',
                index: '/text-to-image',
                title: '文生图',
            },
            {
                id: '12',
                index: '/image-to-image',
                title: '图片转换',
            },
            {
                id: '13',
                index: '/video-to-video',
                title: '视频转换',
            },
        ],
    },
    {
        id: '2',
        title: 'ArtiScope Community',
        index: '2',
        icon: 'ChatDotRound',
        children: [
            {
                id: '21',
                index: '/community',
                title: '社区',
            },
            {
                id: '22',
                index: '/myposts',
                title: '我的帖子',
            },
            {
                id: '23',
                index: '/postcreator',
                title: '发表',
            },
        ],
    },
];