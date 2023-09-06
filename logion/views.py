from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.http import Http404
from django.views.generic.detail import DetailView
from .serializers import (AuthorSerializer, TextSerializer, TextTitleSerializer, SuggestionSerializer, CommentSerializer)
from .models import Author, Text, Suggestion, Comment, CustomUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import exception_handler
# from .bert import all_possibilities
from .getcontext import get_context
import jwt
import os
import requests
# from django.contrib.auth.models import User


from authz.permissions import HasAdminPermission

def index(request):
    return HttpResponse('Hello, world')

class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [HasAdminPermission]


class TextsByAuthorView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, author_pk):
        try:
            return Text.objects.filter(author=author_pk)
        except Text.DoesNotExist:
            raise Http404
             

    def get(self, request, author_pk, format=None):
        texts = self.get_object(author_pk)
        texts = TextTitleSerializer(texts, many=True)
        return Response(texts.data)
    

class TextDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk, offset):
        try:
            text_detail = Text.objects.get(pk=pk)
            suggestions_detials = Suggestion.objects.filter(text=pk)
            return [text_detail, suggestions_detials]
        except Text.DoesNotExist or Suggestion.DoesNotExist:
            raise Http404
             

    def get(self, request, pk, offset, format=None):
        text, suggestions = self.get_object(pk, offset)
        text_serializer = TextSerializer(text)
        suggestions_serializer = SuggestionSerializer(suggestions, many=True)
        chunks = text_serializer.data['body'].split("***")
        updated_body = chunks[offset]
        dummy = { 'id' : text_serializer.data['id'], 'body': updated_body, 'chunks': len(chunks) }
        return Response([dummy, suggestions_serializer.data])
    

class SuggestionCommentsView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, suggestion_pk):
        try:
            return Comment.objects.filter(suggestion=suggestion_pk)
        except Comment.DoesNotExist:
            raise Http404

    def get(self, request, suggestion_pk, format=None):
        comments = self.get_object(suggestion_pk)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    

class GetSuggestionView(APIView):
    permission_classes = [IsAuthenticated]


    # def get(self, request, format=None):
    #     print("starting")
    #     text1 = f"""  ἐπείπερ ἐν τῷ γένει τῶν κατὰ τὸ πρός τι συλλογισμῶν εἰσὶν ὥσπερ οἱ κατὰ τὸ μᾶλλόν τε καὶ ἧττον οὕτως καὶ οἱ κατὰ τὸ ὡσαύτως καὶ ἀνάλογον, επισκεπτ """
    #     text2= f"""καὶ τούτων ἡ πίστις ἐκ τινῶν ἀξιωμάτων ἤρτηται.    (διαφερέτω δὲ μηδὲν ἢ ὡσαύτως εἰπεῖν ἢ ἴσως ἢ ὁμοίως.   ) ἔστι δὲ τοιοῦτος ὁ λόγος οὗτος καὶ Πλάτωνος ἐν τῇ Πολιτείᾳ γεγραμμένος·    ἀξιοῖ γὰρ Σωκράτης ὡς πόλις γίγνεται καὶ λέγεται δικαία οὕτως καὶ ψυχὴν γίγνεσθαί τε καὶ λέγεσθαι δικαίαν, ὡσαύτως δὲ καὶ πρᾶξιν καὶ νόμον καὶ πᾶν ὁτιοῦν τῶν δικαίων εἶναι λεγομένων κατὰ ταὐτὸν λέγεσθαι σημαινόμενον.    τὸ γὰρ εἶδος τῆς δικαιοσύνης ἀφ’ οὗ λέγεται πάντα τὰ κατὰ μέρος δίκαια, τοῦτο μὲν ἓν ἅπασίν ἐστιν·    εἰ δέ ἐστιν ἕν τι καὶ ταὐτὸν ἀφ’ οὗπερ ἂν ἓν τῶν κατὰ μέρος ἐναργῶς ῥηθήσεται, κἀπὶ τἆλλα πάντ᾽ ἐνεχθήσεται, γιγνωσκόντων ἡμῶν οὐ κατ’ ἴσην ἐπὶ πάντων ἐνάργειαν φαίνεσθαι ταὐτὸν εἶδος ἀλλ’ ἐπ’ ἐκείνων μὲν ἐναργέστερον, ἐφ’ ἑτέρων δ’ ἀμυδρότερον.    καὶ διὰ τοῦτο προγυμνάσας τοὺς κοινωνοῦντας αὐτῷ τοῦ λόγου νεανίσκους ἐν τῷ περὶ τῆς δικαίας πόλεως λόγῳ μεταβὰς ἐπὶ τὴν ψυχὴν ἀποδείκνυσι κἀκείνην κατὰ τὸν αὐτὸν τρόπον δικαίαν λεγομένην ὥσπερ καὶ τὴν πόλιν ὡς εἶναι τὸν συλλογισμὸν τοιοῦτον "ὡσαύτως πόλις τε καὶ ψυχὴ δίκαιαί τε λέγονται καί εἰσιν.    πόλις δὲ δικαία λέγεται τῇ τῶν μερῶν αὐτῆς ἰδιοπραγίᾳ.    καὶ ψυχὴ ἄρα κατὰ τοῦτο δικαία λεχθήσεται.   " ἐπεὶ δὲ καὶ κατὰ τὸν αὐτὸν λόγον ἀποδείκνυται πάνυ πολλὰ παρὰ τοῖς ἀριθμητικοῖς καὶ γεωμέτραις καὶ εἴη ἂν προδήλως πᾶσιν ἀνθρώποις φύσει φαινόμενον ὅτιπερ ἂν οὕτως ἀποδειχθῇ πιστὸν εἶναι, διὰ τοῦτο κἀγὼ κατὰ τὰς περὶ τῶν συλλογισμῶν πραγματείας ἔγραψα περὶ τούτου τοῦ συλλογισμοῦ.    παράδειγμα γὰρ τούτου νοηθὲν καὶ τοῖς ἀπείροις ἀριθμητικῆς τε καὶ γεωμετρίας ἔστω τόδε "ὡς τὸ πρῶτον πρὸς τὸ δεύτερον, οὕτως καὶ τὸ τρίτον πρὸς τὸ τέταρτον.    τὸ δὲ πρῶτον τοῦ δευτέρου διπλάσιόν ἐστιν.    τὸ τρίτον ἄρα τοῦ τετάρτου διπλάσιόν ἐστιν."""  
    #     strings = all_possibilities(text1, text2, num_tokens=3, right=False)
    #     return HttpResponse(strings)
    

    def post(self, request, format=None):
        print("starting this")
        text1, text2 = get_context(request.data['words'], request.data['text_id'], request.data['chunk'])
        # text1 = f"""  ἐπείπερ ἐν τῷ γένει τῶν κατὰ τὸ πρός τι συλλογισμῶν εἰσὶν ὥσπερ οἱ κατὰ τὸ μᾶλλόν τε καὶ ἧττον οὕτως καὶ οἱ κατὰ τὸ ὡσαύτως καὶ ἀνάλογον, επισκεπτ """
        # text2= f"""καὶ τούτων ἡ πίστις ἐκ τινῶν ἀξιωμάτων ἤρτηται.    (διαφερέτω δὲ μηδὲν ἢ ὡσαύτως εἰπεῖν ἢ ἴσως ἢ ὁμοίως.   ) ἔστι δὲ τοιοῦτος ὁ λόγος οὗτος καὶ Πλάτωνος ἐν τῇ Πολιτείᾳ γεγραμμένος·    ἀξιοῖ γὰρ Σωκράτης ὡς πόλις γίγνεται καὶ λέγεται δικαία οὕτως καὶ ψυχὴν γίγνεσθαί τε καὶ λέγεσθαι δικαίαν, ὡσαύτως δὲ καὶ πρᾶξιν καὶ νόμον καὶ πᾶν ὁτιοῦν τῶν δικαίων εἶναι λεγομένων κατὰ ταὐτὸν λέγεσθαι σημαινόμενον.    τὸ γὰρ εἶδος τῆς δικαιοσύνης ἀφ’ οὗ λέγεται πάντα τὰ κατὰ μέρος δίκαια, τοῦτο μὲν ἓν ἅπασίν ἐστιν·    εἰ δέ ἐστιν ἕν τι καὶ ταὐτὸν ἀφ’ οὗπερ ἂν ἓν τῶν κατὰ μέρος ἐναργῶς ῥηθήσεται, κἀπὶ τἆλλα πάντ᾽ ἐνεχθήσεται, γιγνωσκόντων ἡμῶν οὐ κατ’ ἴσην ἐπὶ πάντων ἐνάργειαν φαίνεσθαι ταὐτὸν εἶδος ἀλλ’ ἐπ’ ἐκείνων μὲν ἐναργέστερον, ἐφ’ ἑτέρων δ’ ἀμυδρότερον.    καὶ διὰ τοῦτο προγυμνάσας τοὺς κοινωνοῦντας αὐτῷ τοῦ λόγου νεανίσκους ἐν τῷ περὶ τῆς δικαίας πόλεως λόγῳ μεταβὰς ἐπὶ τὴν ψυχὴν ἀποδείκνυσι κἀκείνην κατὰ τὸν αὐτὸν τρόπον δικαίαν λεγομένην ὥσπερ καὶ τὴν πόλιν ὡς εἶναι τὸν συλλογισμὸν τοιοῦτον "ὡσαύτως πόλις τε καὶ ψυχὴ δίκαιαί τε λέγονται καί εἰσιν.    πόλις δὲ δικαία λέγεται τῇ τῶν μερῶν αὐτῆς ἰδιοπραγίᾳ.    καὶ ψυχὴ ἄρα κατὰ τοῦτο δικαία λεχθήσεται.   " ἐπεὶ δὲ καὶ κατὰ τὸν αὐτὸν λόγον ἀποδείκνυται πάνυ πολλὰ παρὰ τοῖς ἀριθμητικοῖς καὶ γεωμέτραις καὶ εἴη ἂν προδήλως πᾶσιν ἀνθρώποις φύσει φαινόμενον ὅτιπερ ἂν οὕτως ἀποδειχθῇ πιστὸν εἶναι, διὰ τοῦτο κἀγὼ κατὰ τὰς περὶ τῶν συλλογισμῶν πραγματείας ἔγραψα περὶ τούτου τοῦ συλλογισμοῦ.    παράδειγμα γὰρ τούτου νοηθὲν καὶ τοῖς ἀπείροις ἀριθμητικῆς τε καὶ γεωμετρίας ἔστω τόδε "ὡς τὸ πρῶτον πρὸς τὸ δεύτερον, οὕτως καὶ τὸ τρίτον πρὸς τὸ τέταρτον.    τὸ δὲ πρῶτον τοῦ δευτέρου διπλάσιόν ἐστιν.    τὸ τρίτον ἄρα τοῦ τετάρτου διπλάσιόν ἐστιν."""  
        API_URL = 'https://jb9v24dhj5eyzpf4.us-east-1.aws.endpoints.huggingface.cloud'
        headers = {
            "Authorization": "Bearer yLFVMjFzKrDuSBOCPxJVmkjDwcHABWjoMjoDdpcCnmILWxVqAAtYpBUCgMDoqhitGdkKabGTpsAFtCoNPpuzmdtfFVcpCvkypGWXlTQhehLfkrYWJhXhgRYVfgAkLUYu",
            "Content-Type": "application/json"
        }

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
        output = query({
            "inputs": f'{text1}[MASK][MASK][MASK][MASK][MASK]{text2}',
        })
        print(output)
        # strings = all_possibilities(text1, text2, num_tokens=3, right=False)
        return HttpResponse(output)
    

class SaveSuggestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        s = Suggestion()
        s.text = Text.objects.get(id = request.data['text_id'])
        s.chunk = request.data['chunk']
        s.suggested_text = request.data['suggestion']
        s.start_index = request.data['start_index']
        s.end_index = request.data['end_index']
        s.original_text = request.data['words']
        bearer_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        domain = os.environ.get('AUTH0_DOMAIN')
        headers = {"Authorization": f'Bearer {bearer_token}'}
        result = requests.get(url=f'https://{domain}/userinfo', headers=headers).json()
        u = CustomUser.objects.get(user_id=result["sub"])
        s.submitter = u
        s.save()
        return HttpResponse("Suggestion Saved")


class SaveCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        c = Comment()
        c.suggestion = Suggestion.objects.get(id = request.data['suggestion_id'])
        c.body = request.data['comment']
        bearer_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        domain = os.environ.get('AUTH0_DOMAIN')
        headers = {"Authorization": f'Bearer {bearer_token}'}
        result = requests.get(url=f'https://{domain}/userinfo', headers=headers).json()
        u = CustomUser.objects.get(user_id=result["sub"])
        c.commenter = u
        c.save()
        return HttpResponse("Suggestion Saved")
    

    
class LoginUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        bearer_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        domain = os.environ.get('AUTH0_DOMAIN')
        headers = {"Authorization": f'Bearer {bearer_token}'}
        result = requests.get(url=f'https://{domain}/userinfo', headers=headers).json()
        # print(result)
        try:
            u = CustomUser.objects.get(user_id=result["sub"])
        except CustomUser.DoesNotExist:
            u = CustomUser.objects.filter(email=result["email"]).first()
            if u is None:
                u = CustomUser()
                u.username=result["nickname"]
                u.email = result["email"]
            u.user_id = result["sub"]
            u.save()
            return HttpResponse('User Created')
        return HttpResponse('Existing User')
        

